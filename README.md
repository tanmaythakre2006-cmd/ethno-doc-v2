<div align="center">
  <img src="https://via.placeholder.com/1200x675/0a0a0a/00ffd1?text=Ethno-Doc-V2+Molecular+Lattice" alt="Ethno-Doc-V2 Hero Banner" width="100%">

  <br><br>

  <span style="font-family: monospace; font-size: 1.2em;">
    <a href="#abstract" style="text-decoration: none; color: #00ffd1;">Abstract</a> |
    <a href="#architecture" style="text-decoration: none; color: #00ffd1;">Architecture</a> |
    <a href="#simulation-metrics" style="text-decoration: none; color: #00ffd1;">Simulation Metrics</a> |
    <a href="#execution" style="text-decoration: none; color: #00ffd1;">Execution</a>
  </span>

  <br><br>

  <img src="https://img.shields.io/badge/FastAPI-005C53?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/AutoDock_Vina-FF9800?style=for-the-badge" alt="AutoDock Vina">
  <img src="https://img.shields.io/badge/PySCF-009688?style=for-the-badge" alt="PySCF">
  <img src="https://img.shields.io/badge/RDKit-FFC107?style=for-the-badge&logo=python&logoColor=black" alt="RDKit">
  <img src="https://img.shields.io/badge/PostgreSQL-112B3C?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
</div>

<br><br>

<h2 id="abstract">I. Abstract & Core Philosophy</h2>

<table border="0" width="100%" cellspacing="0" cellpadding="15">
  <tr>
    <td width="60%" valign="top">
      <p><b>Ethno-Doc-V2</b> represents a paradigm shift in automated <i>in-silico</i> pharmacognosy and molecular dynamics orchestration. Designed as a highly deterministic extraction and simulation engine, the architecture bridges the gap between historical ethnobotanical nomenclature and modern computational chemistry.</p>
      <p>By leveraging a multi-stage pipeline, Ethno-Doc-V2 autonomously drives large-scale target identification, processing raw historical pharmacopeias into validated stereochemical targets, and subsequently submitting them to a rigorous high-throughput virtual screening (HTVS) and molecular dynamics pipeline.</p>
      <p>All internal processing is strictly deterministic. The pipeline operates via explicit open-science REST and SPARQL interfaces, dropping dependency on generative probabilistic layers to guarantee rigid scientific reproducibility.</p>
    </td>
    <td width="40%" align="center" valign="top">
      <img src="https://via.placeholder.com/600x400/0a0a0a/FF9800?text=MD_WaterBox_Simulation.mp4" alt="MD Water-Box Simulation" width="100%" style="border: 1px solid #333; border-radius: 4px;">
      <p style="font-size: 0.8em; font-family: monospace; color: #888;">Fig 1: Real-time explicit solvent trajectory visualization.</p>
    </td>
  </tr>
</table>

<br>

<h2 id="architecture">II. The Architectural Pipeline</h2>

**Phase 1: Ligand Preparation (RDKit) & Pocket Prediction (P2Rank)**
The initial ingestion sequence leverages **RDKit** to normalize SMILES strings, calculate 3D stereochemical embeddings, and enforce protonation states at physiological pH (7.4). Concurrently, **P2Rank** evaluates the apoprotein target, applying random forest algorithms to predict putative allosteric and orthosteric binding pockets based on local chemical neighborhood topology.

**Phase 2: Autonomous Docking (AutoDock Vina) & Toxicity (DeepChem)**
Synthesized targets enter a deterministic docking grid powered by **AutoDock Vina**. The grid performs localized stochastic global optimization using the Broyden-Fletcher-Goldfarb-Shanno (BFGS) method. Post-docking, top poses are routed through **DeepChem** for robust ADMET (Absorption, Distribution, Metabolism, Excretion, and Toxicity) profiling and hepatotoxicity prediction.

**Phase 3: Quantum Descriptors (PySCF) & Molecular Dynamics (OpenMM)**
Surviving ligand-protein complexes are subjected to high-fidelity quantum mechanical evaluation using **PySCF** for density functional theory (DFT) baseline extraction. Ultimately, the system initiates explicit solvent molecular dynamics using **OpenMM**, simulating 100ns trajectories in a TIP3P water box under NPT ensemble parameters.

<br>

<h2 id="simulation-metrics">III. Data Dictionary & Mathematics</h2>

The computational evaluation matrix strictly adheres to the following physical constants and computed descriptors:

**Binding Free Energy ($\Delta G$)**
Derived from AutoDock Vina's empirical scoring function, estimating the thermodynamic affinity of the receptor-ligand complex:

$$ \Delta G = \Delta G_{vdW} + \Delta G_{Hbond} + \Delta G_{elec} + \Delta G_{tor} + \Delta G_{desolv} $$

**Root Mean Square Fluctuation (RMSF)**
A measure of the average deviation of a particle over time, utilized in our OpenMM phase to map localized protein backbone flexibility over the trajectory timeline:

$$ RMSF_i = \sqrt{ \frac{1}{T} \sum_{t=1}^{T} ( r_i(t) - \bar{r}_i )^2 } $$

**HOMO-LUMO Energy Gap**
Extracted via PySCF Density Functional Theory calculations, establishing a metric for molecular kinetic stability, optical polarizability, and chemical reactivity:

$$ E_{gap} = E_{LUMO} - E_{HOMO} $$

<br>

<h2 id="execution">IV. Execution & Quickstart</h2>

### Repository Structure

```text
ethno-doc-v2/
├── api/                     # FastAPI ASGI application routing
├── core/                    # Engine orchestration & configuration
├── molecular_engines/
│   ├── docking_vina.py      # AutoDock Vina grid orchestration
│   ├── qm_pyscf.py          # DFT quantum mechanical descriptors
│   └── md_openmm.py         # OpenMM NPT trajectory simulations
├── local_vault/             # Local SQLite DBs & JSONL airlock files
├── scripts/                 # Bash pipeline orchestration scripts
└── requirements.txt         # Dependency lockfile
```

### Initialization Sequence

Deploy the virtual environment and initialize the primary computation cluster:

```bash
# 1. Clone the repository and establish the computational sandbox
git clone https://github.com/organization/ethno-doc-v2.git
cd ethno-doc-v2

# 2. Deploy Python virtual environment and install molecular dependencies
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Export PYTHONPATH to prevent cross-contamination and start the engine
export PYTHONPATH=$(pwd)/ethno-doc-v2
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

<br>
<hr style="border: 0; height: 1px; background: #333;">

<div align="center" style="font-family: monospace; color: #777; font-size: 0.9em;">
  <p><b>ETHNO-DOC-V2</b> &copy; 2024</p>
  <p><i>Strictly Engineered for Open-Science HTVS Pharmacognosy</i></p>
</div>