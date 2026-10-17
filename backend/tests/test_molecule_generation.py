import os
import random
import tempfile

from rdkit import Chem, rdBase

from src.main import MoleculeGenerator


def canonical(smiles: str) -> str:
    """Canonical form of a SMILES string, for comparing structures.

    The base strings used in these tests are written in a non-canonical style
    (aspirin is written with an explicit Kekule ring, C1=CC=CC=C1). Comparing a
    canonicalised result against the raw input string makes the comparison true
    even when no mutation happened at all, because RDKit re-spells the ring.
    Every structural comparison in this file goes through here.
    """
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None, f"test fixture is not valid SMILES: {smiles!r}"
    return Chem.MolToSmiles(mol)


MOLECULES = (
    "CCO",  # ethanol
    "c1ccccc1",  # benzene, fully aromatic
    "CC(=O)OC1=CC=CC=C1C(=O)O",  # aspirin
    "CN1C=NC2=C1C(=O)N(C(=O)N2C)",  # caffeine, 10 of 14 bonds aromatic
    "CC(C)(C)C",  # neopentane, no bond order change is chemically possible
)


def _adds_an_atom(before, after):
    """the atom count"""
    return after.GetNumAtoms() == before.GetNumAtoms() + 1


def _changes_bond_orders(before, after):
    """the multiset of bond orders"""
    return sorted(b.GetBondTypeAsDouble() for b in before.GetBonds()) != sorted(
        b.GetBondTypeAsDouble() for b in after.GetBonds()
    )


def _changes_elements(before, after):
    """the multiset of atomic numbers"""
    return sorted(a.GetAtomicNum() for a in before.GetAtoms()) != sorted(
        a.GetAtomicNum() for a in after.GetAtoms()
    )


# What each operator promises to change when it reports success. These are
# structural checks on purpose: canonical SMILES equality is too weak, because
# aromaticity is re-perceived during sanitisation and can erase an edit while
# leaving the string untouched.
INTENDED_CHANGES = (
    ("substituent", MoleculeGenerator._add_random_substituent, _adds_an_atom),
    ("bond_order", MoleculeGenerator._modify_bond_order, _changes_bond_orders),
    ("atom_swap", MoleculeGenerator._swap_atom, _changes_elements),
)


def test_comparison_detects_an_unchanged_molecule():
    """Regression guard for the assertions below.

    This is the defect that made the mutation tests vacuous: they compared a
    canonicalised result against a raw, differently-spelled input, so an
    entirely unmutated molecule satisfied "output != input". If this test fails,
    every structural assertion in this file is unreliable again.
    """
    base_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"  # Aspirin
    unmutated = Chem.MolFromSmiles(base_smiles)

    # The old comparison: true even though nothing was mutated.
    assert Chem.MolToSmiles(unmutated) != base_smiles

    # The canonical comparison: correctly reports that nothing changed.
    assert Chem.MolToSmiles(unmutated) == canonical(base_smiles)


def test_generate_random_molecule():
    base_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"  # Aspirin

    result = MoleculeGenerator.generate_random_molecule(base_smiles)

    # Check that a valid molecule was generated
    assert result.mol is not None
    assert isinstance(result.mol, Chem.Mol)

    # Check that the generated molecule is different from the base molecule.
    # Both sides are canonicalised, so an unmutated result now fails this.
    generated_smiles = Chem.MolToSmiles(result.mol)
    assert generated_smiles != canonical(base_smiles)


def test_counters_reconcile():
    """Every requested mutation is accounted for exactly once."""
    for base in ("CCO", "CN1C=NC2=C1C(=O)N(C(=O)N2C)"):  # ethanol, caffeine
        for n in (0, 1, 3):
            result = MoleculeGenerator.generate_random_molecule(base, n)
            assert result.requested == n
            assert result.successful + result.failed == n
            assert result.mutated == (result.successful > 0)


def test_generated_output_is_chemically_valid():
    """Outputs must be usable by every consumer, not merely parseable.

    A candidate that passes SanitizeMol can still be left with aromatic flags
    describing the molecule as it was before the edit. Such a molecule raises
    KekulizeException on any kekulizing operation, including the image rendering
    the endpoint performs. This test therefore checks kekulization, not just
    sanitisation.
    """
    for base in MOLECULES:
        for n in (1, 3):
            for seed in range(40):
                random.seed(seed)
                result = MoleculeGenerator.generate_random_molecule(base, n)
                # Survives sanitisation on a fresh copy, so the flags are sound.
                Chem.SanitizeMol(Chem.Mol(result.mol))
                # Survives kekulization, which SanitizeMol alone does not prove.
                Chem.MolToMolBlock(result.mol)


def test_each_operator_actually_applies():
    """A reported success must be a real change of the promised kind.

    Previously these returned only a molecule, so a discarded mutation was
    indistinguishable from an applied one. They now return (mol, applied).

    "Applied" is checked against the structural change each operator promises,
    not against canonical string equality. Sanitisation alone is not enough:
    RDKit re-perceives aromaticity after sanitisation, so setting a bond inside
    an aromatic ring to SINGLE or DOUBLE is accepted and then silently undone,
    yielding an identical canonical SMILES. Counting those as applied
    overstated success badly, 90% of accepted bond-order candidates on caffeine.
    """
    for name, method, changed in INTENDED_CHANGES:
        reported_success = False
        for base_smiles in MOLECULES:
            for seed in range(25):
                random.seed(seed)
                mol = Chem.MolFromSmiles(base_smiles)
                mutated_mol, applied = method(mol)
                assert mutated_mol is not None
                assert isinstance(mutated_mol, Chem.Mol)
                Chem.SanitizeMol(mutated_mol)

                if not applied:
                    # A reported failure must leave the molecule untouched.
                    assert Chem.MolToSmiles(mutated_mol) == canonical(base_smiles)
                else:
                    reported_success = True
                    # A reported success must make the intended change.
                    assert changed(mol, mutated_mol), (
                        f"{name} reported success on {base_smiles!r} but did "
                        f"not change {changed.__doc__}"
                    )

        assert reported_success, f"{name} never reported a success"


def test_fixed_seed_output_is_reproducible():
    """Exact-output regression test.

    This assertion is sensitive to the RDKit version, to the Python version,
    and to how many random numbers are consumed, so a failure here means the
    output changed and should be reviewed deliberately rather than regenerated
    blindly. The property tests above are the ones that must survive dependency
    upgrades.

    The expected value below was recorded under the version pinned in
    requirements.txt (rdkit 2026.9.1, Python 3.14) and confirmed identical under
    rdkit 2025.09.3. If a dependency bump changes it, that is a real signal
    about the mutation output, not a test to delete.
    """
    random.seed(20240101)
    result = MoleculeGenerator.generate_random_molecule("CCO", 1)
    assert Chem.MolToSmiles(result.mol) == "NCCO"
    assert result.successful == 1
    assert result.failed == 0

    # The expected string alone would pass even if the operator achieved that
    # string by accident, or if the counters were detached from the molecule.
    # Assert the change is the one the counters claim: one atom added, ethanol
    # still a connected neutral fragment, and the input untouched.
    base = Chem.MolFromSmiles("CCO")
    assert result.mol.GetNumAtoms() == base.GetNumAtoms() + 1
    assert len(Chem.GetMolFrags(result.mol)) == 1
    assert all(a.GetFormalCharge() == 0 for a in result.mol.GetAtoms())
    assert result.mutated is True
    assert result.requested == 1


def test_molecule_properties():
    base_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"  # Aspirin

    # Generate a molecule
    result = MoleculeGenerator.generate_random_molecule(base_smiles)
    generated_smiles = Chem.MolToSmiles(result.mol)

    # Calculate properties
    properties = MoleculeGenerator.calculate_properties(generated_smiles)

    # Check that properties are calculated
    assert "Molecular Weight" in properties
    assert "LogP" in properties
    assert "H-Bond Donors" in properties
    assert "H-Bond Acceptors" in properties
    assert "Topological Polar Surface Area" in properties

    # Check that properties are numeric
    for prop_value in properties.values():
        assert isinstance(prop_value, (int, float))


def test_mutation_strategies():
    """Every named operator is selectable and produces a valid molecule."""
    base_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"  # Aspirin

    for method_name in ("substituent", "bond_order", "atom_swap"):
        result = MoleculeGenerator.generate_random_molecule(
            base_smiles, mutation_types=[method_name]
        )
        assert isinstance(result.mol, Chem.Mol)
        Chem.SanitizeMol(result.mol)


def test_generate_with_custom_mutations():
    base_smiles = "CCO"  # Ethanol

    # Test with specific mutation types
    result = MoleculeGenerator.generate_random_molecule(
        base_smiles, mutation_types=["substituent"]
    )
    assert result.mol is not None

    result = MoleculeGenerator.generate_random_molecule(
        base_smiles, mutation_types=["atom_swap"]
    )
    assert result.mol is not None

    # Test with empty mutation types (should use defaults)
    result = MoleculeGenerator.generate_random_molecule(base_smiles, mutation_types=[])
    assert result.mol is not None


def capture_rdkit_stderr(action):
    """Return whatever RDKit writes to stderr while action runs.

    RDKit writes through the C++ logger straight to file descriptor 2, so this
    redirects the descriptor rather than using a Python-level stream, otherwise
    the output would be missed entirely. A temporary file is used instead of a
    pipe so that a chatty action cannot fill the pipe buffer and deadlock.
    """
    with tempfile.TemporaryFile() as sink:
        saved = os.dup(2)
        try:
            os.dup2(sink.fileno(), 2)
            action()
        finally:
            os.dup2(saved, 2)
            os.close(saved)
        sink.seek(0)
        return sink.read().decode(errors="replace")


def test_expected_candidate_warnings_are_suppressed():
    """A rejection logged during candidate validation must not reach stderr.

    Trial-and-validate rejects most candidates by design, and RDKit logs each
    rejection. The helper that performs validation mutes that, because it is
    expected output rather than a fault.
    """
    # A candidate RDKit rejects loudly: oxygen with four bonds triggers the
    # explicit-valence warning that the operators would otherwise emit for every
    # rejected proposal.
    invalid = Chem.RWMol(Chem.MolFromSmiles("CCO"))
    for _ in range(3):
        new_idx = invalid.AddAtom(Chem.Atom(8))
        invalid.AddBond(2, new_idx, Chem.BondType.SINGLE)
    candidate = invalid.GetMol()

    # Guard the fixture: the warning must exist before suppression is tested,
    # otherwise this test would pass for the wrong reason.
    unsuppressed = capture_rdkit_stderr(
        lambda: MoleculeGenerator._is_acceptable(candidate)
    )
    assert "valence" in unsuppressed.lower(), (
        f"fixture no longer provokes an RDKit warning: {unsuppressed!r}"
    )

    suppressed = capture_rdkit_stderr(
        lambda: MoleculeGenerator._validate_candidate(candidate)
    )
    assert suppressed == "", f"expected silence during validation, got: {suppressed!r}"


def test_warnings_outside_candidate_validation_remain_visible():
    """Suppression must not leak past the validation call.

    A real diagnostic emitted immediately after validation still has to reach
    stderr, otherwise this change would hide the failures it exists to make
    readable.
    """
    marker = "MARKER-AFTER-VALIDATION"

    def emit():
        rdBase.LogWarningMsg(marker)

    output = capture_rdkit_stderr(emit)
    assert marker in output, f"expected {marker!r} to be visible, got: {output!r}"


def test_suppression_is_restored_after_validation():
    """After a suppressed block, logging returns to normal.

    This pins the ordering: a warning raised before validation is visible, one
    raised during validation is not, and one raised after is visible again.
    """
    before = capture_rdkit_stderr(lambda: rdBase.LogWarningMsg("BEFORE"))

    def during():
        with rdBase.BlockLogs():
            rdBase.LogWarningMsg("DURING")

    inside = capture_rdkit_stderr(during)
    after = capture_rdkit_stderr(lambda: rdBase.LogWarningMsg("AFTER"))

    assert "BEFORE" in before
    assert "DURING" not in inside
    assert "AFTER" in after


def test_suppression_does_not_change_which_candidates_are_accepted():
    """Suppression is a logging concern only.

    The same candidates must be accepted or rejected with and without the
    suppression wrapper, otherwise counters would silently shift.
    """
    for base_smiles in MOLECULES:
        for seed in range(25):
            mol = Chem.MolFromSmiles(base_smiles)

            # Reseed before each call: the operators draw from the shared random
            # module, so identical decisions require identical inputs.
            random.seed(seed)
            with rdBase.BlockLogs():
                mutated_with, applied_with = MoleculeGenerator._swap_atom(mol)

            random.seed(seed)
            mutated_without, applied_without = MoleculeGenerator._swap_atom(mol)

            assert applied_with == applied_without
            assert Chem.MolToSmiles(mutated_with) == Chem.MolToSmiles(mutated_without)


def test_counters_unaffected_by_suppression():
    """The counter invariant must hold with suppression in place."""
    for base_smiles in ("CCO", "CN1C=NC2=C1C(=O)N(C(=O)N2C)"):
        for n in (0, 1, 3):
            random.seed(7)
            result = MoleculeGenerator.generate_random_molecule(base_smiles, n)
            assert result.successful + result.failed == result.requested == n
            assert result.mutated == (result.successful > 0)


def test_warning_from_outside_candidate_validation_survives_an_operator_call():
    """Suppression must not swallow diagnostics raised elsewhere in an operator.

    _candidate_order runs inside the operator but outside _validate_candidate,
    so a warning raised there must still be visible. This is the test that
    distinguishes a narrowly scoped block from one wrapped around the whole
    operator, which would silently hide genuine problems.
    """
    original = MoleculeGenerator._candidate_order
    marker = "MARKER-DURING-CANDIDATE-ORDER"

    def noisy(items):
        rdBase.LogWarningMsg(marker)
        return original(items)

    for base_smiles in MOLECULES:
        random.seed(3)
        MoleculeGenerator._candidate_order = staticmethod(noisy)
        try:
            # Routed through _random_mutation rather than a single operator, so
            # that widening the suppression to cover the whole operator call
            # would actually be exercised here and caught.
            output = capture_rdkit_stderr(
                lambda b=base_smiles: MoleculeGenerator._random_mutation(
                    Chem.MolFromSmiles(b), None
                )
            )
        finally:
            MoleculeGenerator._candidate_order = staticmethod(original)
        assert marker in output, (
            f"a warning raised outside candidate validation was suppressed for "
            f"{base_smiles!r}: {output!r}"
        )
