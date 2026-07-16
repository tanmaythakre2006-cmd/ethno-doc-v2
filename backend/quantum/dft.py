from pyscf import gto, scf
import numpy as np

def calculate_dft_descriptors(xyz_file: str) -> dict:
    """
    Calculates HOMO and LUMO using Density Functional Theory (DFT) via `pyscf`.
    Explicitly calculates and returns the energy gap: E_gap = E_LUMO - E_HOMO.
    """
    # Parse the XYZ geometry into a PySCF molecule object
    mol = gto.M(
        atom=xyz_file,
        basis='sto-3g',  # Basic minimal basis set for speed
        charge=0,
        spin=0
    )

    # Initialize DFT object using B3LYP functional
    mf = scf.RKS(mol)
    mf.xc = 'b3lyp'

    # Run the self-consistent field calculation
    mf.kernel()

    if not mf.converged:
        raise RuntimeError("DFT calculation did not converge")

    # Extract orbital energies
    energies = mf.mo_energy

    # Find HOMO and LUMO indices
    # Number of occupied orbitals is equal to the number of electrons divided by 2 (for restricted, closed-shell systems)
    homo_idx = mol.nelectron // 2 - 1
    lumo_idx = homo_idx + 1

    homo_energy = energies[homo_idx]
    lumo_energy = energies[lumo_idx]

    # Calculate energy gap
    energy_gap = lumo_energy - homo_energy

    # Convert from Hartrees to eV (1 Hartree = 27.2114 eV)
    hartree_to_ev = 27.211386245988

    return {
        "homo_energy_hartree": homo_energy,
        "lumo_energy_hartree": lumo_energy,
        "energy_gap_hartree": energy_gap,
        "homo_energy_ev": homo_energy * hartree_to_ev,
        "lumo_energy_ev": lumo_energy * hartree_to_ev,
        "energy_gap_ev": energy_gap * hartree_to_ev
    }
