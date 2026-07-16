import asyncio
from vina import Vina

async def run_docking(receptor_pdbqt: str, ligand_pdbqt: str, center: tuple, box_size: tuple = (20, 20, 20)):
    """
    Asynchronous function for docking using `vina`.
    Initializes the `Vina` object, sets the receptor and ligand, computes affinity maps natively,
    and runs `v.dock()`. Extracts and returns the top Binding Affinity (Delta G in kcal/mol) and RMSD.
    """
    v = Vina(sf_name='vina')

    v.set_receptor(receptor_pdbqt)
    v.set_ligand_from_file(ligand_pdbqt)

    # Compute affinity maps
    v.compute_vina_maps(center=center, box_size=box_size)

    # Run the docking simulation
    # Run in a thread to make it truly async without blocking the event loop
    await asyncio.to_thread(v.dock, exhaustiveness=8, n_poses=1)

    # Extract the top pose binding affinity and RMSD
    # v.energies() returns a list of lists. For the top pose (first element),
    # it typically returns [total_score, rmsd_lb, rmsd_ub] or similar depending on vina version.
    energies = v.energies()
    if not energies:
        raise ValueError("Docking failed to produce any poses")

    top_energy = energies[0]

    # In Vina 1.2+, energies() returns a list of tuples/lists:
    # [ (affinity, rmsd_lb, rmsd_ub), ... ]
    binding_affinity = top_energy[0]
    rmsd = top_energy[1] if len(top_energy) > 1 else 0.0

    return {
        "binding_affinity": binding_affinity,
        "rmsd": rmsd
    }
