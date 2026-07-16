import sys
import openmm as mm
from openmm import app
from openmm import unit
import MDAnalysis as mda
from MDAnalysis.analysis import rms, align

def run_md_simulation(complex_pdb: str, output_dcd: str = "trajectory.dcd", output_pdb: str = "final.pdb") -> dict:
    """
    Initializes a protein-ligand complex in a simulated water box with physiological ion concentrations.
    Runs a 1-nanosecond MD production run, and uses MDAnalysis to extract the Radius of Gyration (Rg) and RMSF.
    """
    # 1. Load the PDB file
    pdb = app.PDBFile(complex_pdb)

    # 2. Forcefield Setup
    # Using Amber14 for protein and TIP3P for water
    forcefield = app.ForceField('amber14-all.xml', 'amber14/tip3pfb.xml')

    # 3. Solvate the system and add physiological ions (150 mM NaCl)
    modeller = app.Modeller(pdb.topology, pdb.positions)
    modeller.addSolvent(forcefield, padding=1.0*unit.nanometer, ionicStrength=0.15*unit.molar)

    # 4. Create the OpenMM System
    system = forcefield.createSystem(modeller.topology, nonbondedMethod=app.PME,
                                     nonbondedCutoff=1.0*unit.nanometer, constraints=app.HBonds)

    # 5. Integrator Setup
    # Langevin integrator with 2 fs time step
    temperature = 300 * unit.kelvin
    friction = 1 / unit.picosecond
    timestep = 0.002 * unit.picoseconds
    integrator = mm.LangevinMiddleIntegrator(temperature, friction, timestep)

    # 6. Simulation Setup
    simulation = app.Simulation(modeller.topology, system, integrator)
    simulation.context.setPositions(modeller.positions)

    # 7. Energy Minimization
    print("Minimizing energy...")
    simulation.minimizeEnergy()

    # 8. Production Run
    # 1 nanosecond = 1000 ps = 500,000 steps (with 2 fs timestep)
    steps = 500000

    # Set up reporters
    # Save coordinates every 5000 steps (10 ps) -> 100 frames
    simulation.reporters.append(app.DCDReporter(output_dcd, 5000))
    simulation.reporters.append(app.StateDataReporter(sys.stdout, 50000, step=True,
                                                      potentialEnergy=True, temperature=True))

    print("Running 1 ns MD simulation...")
    simulation.step(steps)
    print("Simulation complete.")

    # Save the final positions
    positions = simulation.context.getState(getPositions=True).getPositions()
    with open(output_pdb, 'w') as f:
        app.PDBFile.writeFile(simulation.topology, positions, f)

    # 9. Analysis using MDAnalysis
    # Load trajectory
    u = mda.Universe(output_pdb, output_dcd)

    # Select protein atoms for analysis
    protein = u.select_atoms("protein")

    # Align trajectory to the first frame
    align.AlignTraj(u, u, select="protein and name CA", in_memory=True).run()

    # Calculate Radius of Gyration (Rg)
    rg_values = []
    for ts in u.trajectory:
        rg_values.append(protein.radius_of_gyration())

    avg_rg = sum(rg_values) / len(rg_values)

    # Calculate Root Mean Square Fluctuation (RMSF) for C-alpha atoms
    calphas = protein.select_atoms("name CA")
    R = rms.RMSF(calphas).run()
    rmsf_values = R.results.rmsf
    avg_rmsf = sum(rmsf_values) / len(rmsf_values)

    return {
        "avg_rg_angstrom": avg_rg,
        "avg_rmsf_angstrom": avg_rmsf,
        "rg_trajectory": rg_values,
        "rmsf_per_residue": rmsf_values.tolist()
    }
