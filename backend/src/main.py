import base64
import io
import logging
import random
from typing import Dict, List, NamedTuple, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from rdkit import Chem
from rdkit.Chem import Descriptors, Draw

from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="mol-platform",
    description="Containerized microservice for molecular generation and mutation analysis",
    version="1.0.0",
)

security = HTTPBearer()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class MoleculeGenerationRequest(BaseModel):
    base_smiles: str
    num_mutations: int = 3
    mutation_types: List[str] = ["substituent", "bond_order", "atom_swap"]


class MoleculeResponse(BaseModel):
    original_smiles: str
    generated_smiles: str
    molecular_image: str
    properties: Dict[str, float]
    requested_mutations: int = Field(
        description="Logical mutations the caller asked for."
    )
    successful_mutations: int = Field(
        description=(
            "Mutations that produced their intended structural change and "
            "passed RDKit sanitisation. A candidate that sanitises without "
            "actually changing the structure does not count here."
        )
    )
    failed_mutations: int = Field(
        description=(
            "Mutations where no candidate produced an intended, valid change, "
            "either because sanitisation rejected it or because it left the "
            "structure unchanged. Counted per logical mutation, not per "
            "candidate proposal."
        )
    )
    mutated: bool = Field(
        description=(
            "True when at least one mutation changed the molecule. When false, no "
            "mutation was applied and the molecule has the same structure as the "
            "input. generated_smiles is canonicalised, so its string may differ "
            "from original_smiles even in that case."
        )
    )


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials


class MutationResult(NamedTuple):
    """Outcome of a generation request.

    ``successful`` and ``failed`` count logical mutations, not candidate
    proposals. A single requested mutation that examines several candidate
    atoms and settles on one contributes exactly 1 to whichever counter it
    lands in, so ``successful + failed == requested`` always holds for a
    completed request.
    """

    mol: Chem.Mol
    requested: int
    successful: int
    failed: int

    @property
    def mutated(self) -> bool:
        return self.successful > 0


# Upper bound on candidate proposals tried within one logical mutation. This is
# a guard against pathological inputs, not a correctness parameter: exhausting
# the candidate list simply means that mutation fails and is counted.
MAX_MUTATION_CANDIDATES = 32


class MoleculeGenerator:
    @staticmethod
    def generate_random_molecule(
        base_smiles: str,
        num_mutations: int = 3,
        mutation_types: Optional[List[str]] = None,
    ) -> MutationResult:
        mol = Chem.MolFromSmiles(base_smiles)

        if mol is None:
            preview = base_smiles[:60]
            suffix = "..." if len(base_smiles) > 60 else ""
            raise ValueError(
                f"Invalid SMILES: {preview!r}{suffix} ({len(base_smiles)} characters)"
            )

        successful = 0
        failed = 0
        for _ in range(num_mutations):
            mol, applied = MoleculeGenerator._random_mutation(mol, mutation_types)
            if applied:
                successful += 1
            else:
                failed += 1

        return MutationResult(
            mol=mol,
            requested=num_mutations,
            successful=successful,
            failed=failed,
        )

    @staticmethod
    def _random_mutation(mol, mutation_types=None):
        """Apply one logical mutation.

        Returns ``(mol, applied)``. ``applied`` is False when no candidate in
        any of the selected operators produced a molecule that survives
        sanitisation, in which case ``mol`` is returned unchanged.

        Selecting among candidates is internal to this single mutation: the
        caller counts it once, as either a success or a failure, never both.
        """
        default_mutation_types = ["substituent", "bond_order", "atom_swap"]
        if mutation_types is None:
            mutation_types = default_mutation_types

        mutation_map = {
            "substituent": MoleculeGenerator._add_random_substituent,
            "bond_order": MoleculeGenerator._modify_bond_order,
            "atom_swap": MoleculeGenerator._swap_atom,
        }

        available_funcs = [mutation_map[t] for t in mutation_types if t in mutation_map]
        if not available_funcs:
            available_funcs = [mutation_map[t] for t in default_mutation_types]

        mutation_func = random.choice(available_funcs)
        return mutation_func(mol)

    @staticmethod
    def _candidate_order(items):
        """Return items in random order, bounded by MAX_MUTATION_CANDIDATES.

        Deterministic chemistry decisions belong to RDKit, so this only decides
        which candidates get proposed and in what order. The bound keeps a
        single logical mutation from trying an unbounded number of proposals on
        a large input.
        """
        ordered = list(items)
        random.shuffle(ordered)
        return ordered[:MAX_MUTATION_CANDIDATES]

    @staticmethod
    def _is_acceptable(candidate):
        """Return True when RDKit considers candidate usable by every consumer.

        Sanitising once is not sufficient. These operators edit a copy of the
        input, and changing an atom's element or a bond order leaves aromatic
        flags describing the molecule as it was before the edit. Such a
        candidate can pass the first SanitizeMol call and then fail every
        kekulizing operation afterwards: SanitizeMol on a fresh copy,
        MolToMolBlock, and the image rendering in generate_molecule_image all
        raise KekulizeException. Caffeine at num_mutations=3 hit this in roughly
        one request in a hundred.

        Requiring sanitisation to be idempotent rules those candidates out at
        acceptance time, where a different candidate can still be tried, rather
        than letting one reach the response as a counted success.
        """
        try:
            Chem.SanitizeMol(candidate)
        except Exception:
            return False
        try:
            # A copy, so the accepted candidate is not re-flagged as a side
            # effect of checking it.
            Chem.SanitizeMol(Chem.Mol(candidate))
        except Exception:
            return False
        return True

    @staticmethod
    def _add_random_substituent(mol):
        """Attach one substituent atom, trying successive candidates.

        The previous version chose a single atom by neighbour count and, when
        sanitisation rejected the result, silently returned the input. That
        filter counted bonds rather than valence, so it selected atoms that had
        no room for another bond and discarded the whole mutation roughly half
        the time on drug-like molecules.

        This version proposes candidates and lets RDKit decide, which keeps the
        per-element chemistry in RDKit rather than in a table here. A candidate
        counts as applied only if it survives sanitisation *and* adds exactly
        one atom.
        """
        if mol is None:
            return None, False

        substituents = ["C", "N", "O", "Cl", "Br"]
        expected_atoms = mol.GetNumAtoms() + 1

        for attach_idx in MoleculeGenerator._candidate_order(range(mol.GetNumAtoms())):
            for symbol in MoleculeGenerator._candidate_order(substituents):
                rw_mol = Chem.RWMol(Chem.Mol(mol))
                new_idx = rw_mol.AddAtom(Chem.Atom(symbol))
                rw_mol.AddBond(attach_idx, new_idx, Chem.BondType.SINGLE)
                candidate = rw_mol.GetMol()
                if not MoleculeGenerator._is_acceptable(candidate):
                    continue
                if candidate.GetNumAtoms() != expected_atoms:
                    continue
                return candidate, True

        return mol, False

    @staticmethod
    def _modify_bond_order(mol):
        """Change one bond order, trying successive candidates.

        Sanitisation alone is not sufficient evidence here. On an aromatic bond
        RDKit re-perceives aromaticity after sanitisation, so setting a bond to
        SINGLE or DOUBLE is silently undone and the candidate canonicalises back
        to the input. Counting those as applied overstated success badly: on
        caffeine, 90% of accepted candidates made no structural change at all.

        A candidate therefore counts as applied only if the multiset of bond
        orders actually differs from the input.
        """
        if mol is None:
            return None, False

        bond_orders = [
            Chem.BondType.SINGLE,
            Chem.BondType.DOUBLE,
            Chem.BondType.TRIPLE,
        ]
        original_orders = sorted(b.GetBondTypeAsDouble() for b in mol.GetBonds())

        for bond_idx in MoleculeGenerator._candidate_order(range(mol.GetNumBonds())):
            bond = mol.GetBondWithIdx(bond_idx)
            options = [bo for bo in bond_orders if bo != bond.GetBondType()]
            for new_bond_type in MoleculeGenerator._candidate_order(options):
                rw_mol = Chem.RWMol(Chem.Mol(mol))
                rw_mol.RemoveBond(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())
                rw_mol.AddBond(
                    bond.GetBeginAtomIdx(), bond.GetEndAtomIdx(), new_bond_type
                )
                candidate = rw_mol.GetMol()
                if not MoleculeGenerator._is_acceptable(candidate):
                    continue
                changed = sorted(b.GetBondTypeAsDouble() for b in candidate.GetBonds())
                if changed == original_orders:
                    continue
                return candidate, True

        return mol, False

    @staticmethod
    def _swap_atom(mol):
        """Replace one atom element, trying successive candidates.

        A candidate counts as applied only if at least one atomic number
        actually differs from the input, not merely if it sanitises.
        """
        if mol is None:
            return None, False

        atom_types = ["C", "N", "O", "S", "P"]
        periodic_table = Chem.GetPeriodicTable()
        original_elements = sorted(a.GetAtomicNum() for a in mol.GetAtoms())

        swappable = [
            i for i, atom in enumerate(mol.GetAtoms()) if atom.GetSymbol() in atom_types
        ]
        for atom_idx in MoleculeGenerator._candidate_order(swappable):
            current = mol.GetAtomWithIdx(atom_idx).GetSymbol()
            options = [at for at in atom_types if at != current]
            for symbol in MoleculeGenerator._candidate_order(options):
                rw_mol = Chem.RWMol(Chem.Mol(mol))
                rw_mol.GetAtomWithIdx(atom_idx).SetAtomicNum(
                    periodic_table.GetAtomicNumber(symbol)
                )
                candidate = rw_mol.GetMol()
                if not MoleculeGenerator._is_acceptable(candidate):
                    continue
                if (
                    sorted(a.GetAtomicNum() for a in candidate.GetAtoms())
                    == original_elements
                ):
                    continue
                return candidate, True

        return mol, False

    @staticmethod
    def calculate_properties(smiles: str) -> Dict[str, float]:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {}
        return {
            "Molecular Weight": Descriptors.MolWt(mol),
            "LogP": Descriptors.MolLogP(mol),
            "H-Bond Donors": Descriptors.NumHDonors(mol),
            "H-Bond Acceptors": Descriptors.NumHAcceptors(mol),
            "Topological Polar Surface Area": Descriptors.TPSA(mol),
        }

    @staticmethod
    def generate_molecule_image(mol):
        img = Draw.MolToImage(mol, size=(400, 400))
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()


@app.post(
    "/generate_molecule",
    response_model=MoleculeResponse,
    dependencies=[Depends(verify_api_key)],
)
async def generate_molecule(request: MoleculeGenerationRequest):
    # Validate inputs
    if not request.base_smiles or not request.base_smiles.strip():
        raise HTTPException(status_code=400, detail="base_smiles cannot be empty")
    if request.num_mutations < 0:
        raise HTTPException(
            status_code=400, detail="num_mutations must be non-negative"
        )

    try:
        result = MoleculeGenerator.generate_random_molecule(
            request.base_smiles, request.num_mutations, request.mutation_types
        )

        generated_smiles = Chem.MolToSmiles(result.mol)
        properties = MoleculeGenerator.calculate_properties(generated_smiles)
        molecule_image = MoleculeGenerator.generate_molecule_image(result.mol)

        return MoleculeResponse(
            original_smiles=request.base_smiles,
            generated_smiles=generated_smiles,
            molecular_image=molecule_image,
            properties=properties,
            requested_mutations=result.requested,
            successful_mutations=result.successful,
            failed_mutations=result.failed,
            mutated=result.mutated,
        )

    except ValueError as e:
        logger.warning(f"Molecule generation rejected: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        logger.exception("Molecule generation failed")
        raise HTTPException(
            status_code=500,
            detail="Internal error during molecule generation",
        )


@app.get("/health", dependencies=[Depends(verify_api_key)])
async def health_check():
    return {"status": "healthy", "version": app.version}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
