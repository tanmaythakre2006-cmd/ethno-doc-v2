import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import Descriptors

def prepare_ligand(smiles: str):
    """
    Accepts a SMILES string, generates 3D conformers using the ETKDG algorithm,
    and calculates Lipinski parameters (Molecular Weight, TPSA, number of rotatable bonds, and log P).
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("Invalid SMILES string")

    # Add hydrogens
    mol_with_h = Chem.AddHs(mol)

    # Generate 3D conformers using ETKDG algorithm
    params = AllChem.ETKDG()
    res = AllChem.EmbedMolecule(mol_with_h, params)

    if res != 0:
        raise ValueError("Failed to generate 3D conformer")

    # Calculate Lipinski parameters
    mw = Descriptors.MolWt(mol)
    tpsa = Descriptors.TPSA(mol)
    rotatable_bonds = Descriptors.NumRotatableBonds(mol)
    log_p = Descriptors.MolLogP(mol)

    return {
        "conformer": mol_with_h,
        "mw": mw,
        "tpsa": tpsa,
        "rotatable_bonds": rotatable_bonds,
        "log_p": log_p
    }
