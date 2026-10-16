import base64
import io
import logging
import random
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
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


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials


class MoleculeGenerator:
    @staticmethod
    def generate_random_molecule(
        base_smiles: str,
        num_mutations: int = 3,
        mutation_types: Optional[List[str]] = None,
    ) -> Chem.Mol:
        base_mol = Chem.MolFromSmiles(base_smiles)

        if base_mol is None:
            raise ValueError(f"Invalid SMILES: {base_smiles}")

        mol = Chem.MolFromSmiles(base_smiles)

        for _ in range(num_mutations):
            mol = MoleculeGenerator._random_mutation(mol, mutation_types)

        return mol

    @staticmethod
    def _random_mutation(mol, mutation_types=None):
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
    def _add_random_substituent(mol):
        # Ensure input is a valid molecule
        if mol is None:
            return None

        try:
            # Possible substituents (single atoms for simplicity)
            substituents = ["C", "N", "O", "Cl", "Br"]

            # Find atoms where substituents can be added
            attachable_atoms = [
                i
                for i, atom in enumerate(mol.GetAtoms())
                if atom.GetDegree() < 4  # Limit to atoms with fewer than 4 bonds
            ]

            # If no attachable atoms, return original molecule
            if not attachable_atoms:
                return mol

            # Randomly select an atom to attach substituent
            attach_atom_idx = random.choice(attachable_atoms)
            substituent_symbol = random.choice(substituents)

            # Create editable molecule
            rw_mol = Chem.RWMol(mol)

            # Add new atom
            new_atom = Chem.Atom(substituent_symbol)
            new_idx = rw_mol.AddAtom(new_atom)

            # Add bond between attach atom and new atom
            rw_mol.AddBond(attach_atom_idx, new_idx, Chem.BondType.SINGLE)

            # Get immutable molecule
            modified_mol = rw_mol.GetMol()
            try:
                Chem.SanitizeMol(modified_mol)
                return modified_mol
            except Exception:
                return mol
        except Exception as e:
            print(f"Error in _add_random_substituent: {e}")
            return mol

    @staticmethod
    def _modify_bond_order(mol):
        # Ensure input is a valid molecule
        if mol is None:
            return None

        try:
            # Convert mol to a canonical SMILES
            mol_smiles = Chem.MolToSmiles(mol, isomericSmiles=True)
            mol = Chem.MolFromSmiles(mol_smiles)

            # Get all bonds
            bonds = mol.GetBonds()
            if not bonds:
                return mol

            # Randomly select a bond
            bond_to_modify = random.choice(bonds)

            # Prepare bond order options
            bond_orders = [
                Chem.BondType.SINGLE,
                Chem.BondType.DOUBLE,
                Chem.BondType.TRIPLE,
            ]

            # Remove the current bond order
            current_bond_type = bond_to_modify.GetBondType()
            bond_orders = [bo for bo in bond_orders if bo != current_bond_type]

            # Select a new bond order
            new_bond_type = random.choice(bond_orders)

            # Create an editable molecule
            rw_mol = Chem.RWMol(mol)

            # Modify the bond
            start_atom = int(bond_to_modify.GetBeginAtomIdx())
            end_atom = int(bond_to_modify.GetEndAtomIdx())

            # Remove the existing bond
            rw_mol.RemoveBond(start_atom, end_atom)

            # Add a new bond with the modified order
            rw_mol.AddBond(start_atom, end_atom, new_bond_type)

            # Convert back to immutable molecule
            modified_mol = rw_mol.GetMol()
            try:
                Chem.SanitizeMol(modified_mol)
                return modified_mol
            except Exception:
                return mol
        except Exception as e:
            print(f"Error in _modify_bond_order: {e}")
            return mol

    @staticmethod
    def _swap_atom(mol):
        # Ensure input is a valid molecule
        if mol is None:
            return None

        try:
            # Get atom types to swap
            atom_types = ["C", "N", "O", "S", "P"]

            # Find atoms that can be swapped
            swappable_atoms = [
                i
                for i, atom in enumerate(mol.GetAtoms())
                if atom.GetSymbol() in atom_types
            ]

            # If no swappable atoms, return original molecule
            if not swappable_atoms:
                return mol

            # Randomly select an atom to swap
            atom_to_swap_idx = random.choice(swappable_atoms)
            current_atom = mol.GetAtomWithIdx(atom_to_swap_idx).GetSymbol()

            # Get possible swap atoms (excluding current atom)
            swap_options = [at for at in atom_types if at != current_atom]
            new_atom_symbol = random.choice(swap_options)

            # Create editable molecule and swap atom
            rw_mol = Chem.RWMol(mol)
            pt = Chem.GetPeriodicTable()
            rw_mol.GetAtomWithIdx(atom_to_swap_idx).SetAtomicNum(
                pt.GetAtomicNumber(new_atom_symbol)
            )

            # Get immutable molecule
            modified_mol = rw_mol.GetMol()
            try:
                Chem.SanitizeMol(modified_mol)
                return modified_mol
            except Exception:
                return mol
        except Exception as e:
            print(f"Error in _swap_atom: {e}")
            return mol

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
        generator = MoleculeGenerator()

        # Generate molecule
        generated_mol = generator.generate_random_molecule(
            request.base_smiles, request.num_mutations, request.mutation_types
        )

        # Convert to SMILES
        generated_smiles = Chem.MolToSmiles(generated_mol)

        # Calculate properties
        properties = generator.calculate_properties(generated_smiles)

        # Generate molecule image
        molecule_image = generator.generate_molecule_image(generated_mol)

        return MoleculeResponse(
            original_smiles=request.base_smiles,
            generated_smiles=generated_smiles,
            molecular_image=molecule_image,
            properties=properties,
        )

    except Exception as e:
        logger.error(f"Molecule generation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health", dependencies=[Depends(verify_api_key)])
async def health_check():
    return {"status": "healthy", "version": app.version}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
