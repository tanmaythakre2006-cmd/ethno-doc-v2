// 3Dmol.js rendering and client-side hardware protection
let viewer = null;

function initializeViewer(elementId) {
    const container = document.getElementById(elementId);
    if (!container) return;

    const config = {
        backgroundColor: '#000000',
        antialias: true
    };

    viewer = $3Dmol.createViewer(container, config);
    return viewer;
}

function loadProtein(pdbData) {
    if (!viewer) {
        initializeViewer('mol-viewer');
    }

    if (!viewer || !pdbData) return;

    // Estimate atom count
    const atomCount = countAtoms(pdbData);
    console.log(`Estimated atom count: ${atomCount}`);

    // Update UI
    const molStats = document.getElementById('mol-stats');
    if (molStats) {
        molStats.innerText = `Atoms: ${atomCount} | Rendering...`;
    }

    viewer.clear();
    viewer.addModel(pdbData, "pdb");

    // The Safeguard: Enforce LOD for low-spec/high-atom count
    if (atomCount > 15000) {
        console.warn("High atom count detected. Enforcing cartoon-only LOD.");
        viewer.setStyle({}, { cartoon: { color: 'spectrum' } });
        if (molStats) {
            molStats.innerText = `Atoms: ${atomCount} | Render: Cartoon (LOD enforced)`;
        }
    } else {
        // Standard view: cartoon for backbone, stick for heteroatoms/ligands
        viewer.setStyle({}, { cartoon: { color: 'spectrum' } });
        // viewer.setStyle({hetflag: true}, {stick: {}}); // Optional if needed
        if (molStats) {
            molStats.innerText = `Atoms: ${atomCount} | Render: Standard`;
        }
    }

    viewer.zoomTo();
    viewer.render();
}

function countAtoms(pdbData) {
    // Simple heuristic: count lines starting with ATOM or HETATM
    const lines = pdbData.split('\n');
    let count = 0;
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].startsWith("ATOM  ") || lines[i].startsWith("HETATM")) {
            count++;
        }
    }
    return count;
}

// Helper to fetch PDB from ID (for demonstration, as API isn't built yet)
async function loadProteinData(nodeData) {
    const molTitle = document.getElementById('mol-title');
    if (molTitle) {
        molTitle.innerText = `Loading ${nodeData.name || nodeData.id}...`;
    }

    // In a real scenario, nodeData might contain the PDB string directly or an ID to fetch
    if (nodeData.pdb) {
        loadProtein(nodeData.pdb);
    } else if (nodeData.pdbId) {
        try {
            const response = await fetch(`https://files.rcsb.org/view/${nodeData.pdbId}.pdb`);
            if (!response.ok) throw new Error("PDB fetch failed");
            const pdbStr = await response.text();
            loadProtein(pdbStr);
        } catch (error) {
            console.error("Failed to load PDB:", error);
            if (molTitle) molTitle.innerText = `Failed to load ${nodeData.name}`;
        }
    } else {
        if (molTitle) molTitle.innerText = `No structural data for ${nodeData.name}`;
    }
}

// Bind to window
window.initializeViewer = initializeViewer;
window.loadProtein = loadProtein;
window.loadProteinData = loadProteinData;

document.addEventListener('DOMContentLoaded', () => {
    initializeViewer('mol-viewer');
});
