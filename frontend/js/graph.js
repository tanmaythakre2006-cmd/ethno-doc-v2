// D3.js Force-Directed Graph Initialization
let svg, simulation, link, node, labels;
let graphData = { nodes: [], links: [] };

function initGraph(data) {
    graphData = data;
    const container = document.getElementById('network-graph');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Clear existing
    d3.select("#network-graph").selectAll("*").remove();

    svg = d3.select("#network-graph")
        .append("svg")
        .attr("width", "100%")
        .attr("height", "100%")
        .call(d3.zoom().on("zoom", (event) => {
            svg.selectAll('g').attr('transform', event.transform);
        }))
        .append("g");

    simulation = d3.forceSimulation(graphData.nodes)
        .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2));

    updateGraph();
}

function updateGraph() {
    // Links
    link = svg.selectAll(".link")
        .data(graphData.links, d => d.source.id + "-" + d.target.id);

    link.exit().remove();

    const linkEnter = link.enter().append("line")
        .attr("class", "link")
        .attr("stroke-width", 2);

    link = linkEnter.merge(link);

    // Nodes
    node = svg.selectAll(".node")
        .data(graphData.nodes, d => d.id);

    node.exit().remove();

    const nodeEnter = node.enter().append("circle")
        .attr("class", "node")
        .attr("r", d => getNodeSize(d.type))
        .attr("fill", d => getNodeColor(d.type))
        .call(drag(simulation))
        .on("click", handleNodeClick);

    node = nodeEnter.merge(node);

    // Labels
    labels = svg.selectAll(".node-label")
        .data(graphData.nodes, d => d.id);

    labels.exit().remove();

    const labelsEnter = labels.enter().append("text")
        .attr("class", "node-label")
        .attr("dx", 12)
        .attr("dy", 4)
        .text(d => d.name || d.id);

    labels = labelsEnter.merge(labels);

    simulation.nodes(graphData.nodes).on("tick", ticked);
    simulation.force("link").links(graphData.links);
    simulation.alpha(1).restart();
}

function ticked() {
    link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

    node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);

    labels
        .attr("x", d => d.x)
        .attr("y", d => d.y);
}

// Drag functionality
function drag(simulation) {
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    return d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
}

// Styling helpers
function getNodeColor(type) {
    const colors = {
        'Plant': '#4caf50',
        'Book': '#795548',
        'Claim': '#9c27b0',
        'Chemical': '#ffb800', // neon-amber
        'Target': '#66fcf1'    // neon-cyan
    };
    return colors[type] || '#fff';
}

function getNodeSize(type) {
    const sizes = {
        'Plant': 15,
        'Book': 10,
        'Claim': 8,
        'Chemical': 12,
        'Target': 20
    };
    return sizes[type] || 10;
}

function handleNodeClick(event, d) {
    if (d.type === 'Target' || d.type === 'Chemical') {
        // Trigger 3D rendering if node contains PDB data or ID
        if (typeof window.loadProteinData === 'function') {
            window.loadProteinData(d);
        }
    }
}

// Export / global binding
window.initGraph = initGraph;
window.updateGraph = updateGraph;
window.graphData = graphData;
