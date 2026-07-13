// Client-side DOM and graph manipulation to hide dead data
function pruneNetwork(currentGraphData, filterCriteria) {
    if (!filterCriteria || !filterCriteria.verifiedTargetsOnly) {
        // Return original or don't prune if flag is off
        return currentGraphData;
    }

    // A node leads to a verified molecular target if it is a target itself,
    // or if it connects (directly or indirectly) to a 'Target' node.
    // We will do a simple BFS/DFS from all 'Target' nodes backwards.

    const targetNodes = currentGraphData.nodes.filter(n => n.type === 'Target');
    if (targetNodes.length === 0) {
        // No targets, if verified targets only, nothing is kept (or everything is kept if this means data has no targets yet)
        return { nodes: [], links: [] };
    }

    const connectedNodeIds = new Set();
    const queue = targetNodes.map(n => n.id);
    queue.forEach(id => connectedNodeIds.add(id));

    // Build adjacency list for reverse traversal (undirected graph technically, so forward/backward is same)
    const adjList = {};
    currentGraphData.nodes.forEach(n => {
        adjList[n.id] = [];
    });

    currentGraphData.links.forEach(l => {
        const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
        const targetId = typeof l.target === 'object' ? l.target.id : l.target;

        adjList[sourceId].push(targetId);
        adjList[targetId].push(sourceId);
    });

    // BFS to find all connected nodes
    let head = 0;
    while (head < queue.length) {
        const currentId = queue[head++];
        const neighbors = adjList[currentId] || [];
        for (const neighborId of neighbors) {
            if (!connectedNodeIds.has(neighborId)) {
                connectedNodeIds.add(neighborId);
                queue.push(neighborId);
            }
        }
    }

    const newNodes = currentGraphData.nodes.filter(n => connectedNodeIds.has(n.id));
    const newLinks = currentGraphData.links.filter(l => {
        const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
        const targetId = typeof l.target === 'object' ? l.target.id : l.target;
        return connectedNodeIds.has(sourceId) && connectedNodeIds.has(targetId);
    });

    // Update global graph data object so D3 can bind properly
    // Note: We need to modify the arrays in place or assign new arrays and re-init
    // If updateGraph is robust, assigning new arrays and calling updateGraph is fine
    window.graphData.nodes = newNodes;
    window.graphData.links = newLinks;

    // Call the global updateGraph if it exists
    if (typeof window.updateGraph === 'function') {
        window.updateGraph();
    }

    return { nodes: newNodes, links: newLinks };
}

// Bind to window
window.pruneNetwork = pruneNetwork;

// Example event listener for the filter checkbox
document.addEventListener('DOMContentLoaded', () => {
    const filterCheckbox = document.getElementById('filter-verified');
    if (filterCheckbox) {
        filterCheckbox.addEventListener('change', (e) => {
            const isChecked = e.target.checked;
            // Assuming window.originalGraphData holds the full dataset
            if (window.originalGraphData) {
                // Restore original data before pruning
                window.graphData.nodes = [...window.originalGraphData.nodes];
                window.graphData.links = [...window.originalGraphData.links];

                pruneNetwork(window.graphData, { verifiedTargetsOnly: isChecked });
            }
        });
    }
});
