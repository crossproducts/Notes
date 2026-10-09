/**
 * notes-arch - a draw.io plugin for the Notes repo.
 *
 * Adds a "Notes / Architecture" palette whose shapes match the systems these
 * notes keep describing (API gateways, EKS, agents, observability, data) and
 * sets the default vertex/edge styles so hand-drawn shapes match the palette.
 *
 * Loaded by hediet.vscode-drawio via .vscode/settings.json. The extension asks
 * once per fingerprint before running it; see Architecture/Diagrams/drawio-plugin.md.
 */
Draw.loadPlugin(function (ui) {
  var sb = ui.sidebar;
  var graph = ui.editor.graph;

  // --- design tokens -------------------------------------------------------
  // Light fills with saturated strokes: readable on the white canvas and when
  // exported to .drawio.svg and embedded in markdown.
  var C = {
    edge:    { fill: '#E8EEF9', stroke: '#2F5BB7' }, // entry points, clients
    compute: { fill: '#E7F3EA', stroke: '#2E7D4F' }, // services, functions
    data:    { fill: '#FBF0DC', stroke: '#A8741A' }, // stores, caches, buckets
    async:   { fill: '#F3E9F7', stroke: '#7B3FA0' }, // queues, topics, streams
    ai:      { fill: '#E9F2F6', stroke: '#1F7A8C' }, // models, agents, vectors
    ops:     { fill: '#F0F0F3', stroke: '#5A5A66' }, // observability, CI/CD
    zone:    { fill: 'none',    stroke: '#9AA0AC' }  // boundaries, VPCs
  };

  var BASE = 'rounded=1;arcSize=8;whiteSpace=wrap;html=1;fontSize=12;' +
             'fontColor=#1A1A1A;strokeWidth=1.5;';

  function box(c, extra) {
    return BASE + 'fillColor=' + c.fill + ';strokeColor=' + c.stroke + ';' + (extra || '');
  }

  function shape(name, c, extra) {
    return 'shape=' + name + ';whiteSpace=wrap;html=1;fontSize=12;fontColor=#1A1A1A;' +
           'strokeWidth=1.5;fillColor=' + c.fill + ';strokeColor=' + c.stroke + ';' +
           (extra || '');
  }

  // --- palette entries -----------------------------------------------------
  // [style, width, height, label, tooltip, search tags]
  var vertices = [
    // entry / edge
    [box(C.edge, 'arcSize=30;'), 120, 50, 'Client',
      'Browser, mobile or CLI caller', 'client user browser caller'],
    [box(C.edge), 150, 50, 'API Gateway',
      'HTTP entry point', 'api gateway alb ingress http'],
    [box(C.edge, 'dashed=1;'), 150, 50, 'mTLS Edge',
      'Mutual-TLS terminating edge', 'mtls tls edge zero trust certificate'],
    [box(C.edge), 140, 50, 'Load Balancer',
      'L4/L7 load balancer', 'lb alb nlb load balancer'],

    // compute
    [box(C.compute), 140, 60, 'Service',
      'Long-running service', 'service microservice app api'],
    [box(C.compute, 'arcSize=40;'), 130, 50, 'Function',
      'Serverless function', 'lambda function serverless faas'],
    [box(C.compute, 'dashed=1;dashPattern=8 4;'), 140, 50, 'Job',
      'Batch job or cron task', 'job batch cron task worker'],
    [box(C.compute, 'container=1;collapsible=0;verticalAlign=top;spacingTop=6;fillColor=none;'),
      240, 160, 'Pod',
      'Kubernetes pod (drop containers inside)', 'pod kubernetes k8s eks container'],

    // data
    [shape('cylinder3', C.data, 'boundedLbl=1;backgroundOutline=1;size=12;'), 110, 80, 'Database',
      'Relational or document store', 'db database rds postgres dynamo store'],
    [shape('cylinder3', C.data, 'boundedLbl=1;backgroundOutline=1;size=12;'), 100, 70, 'Cache',
      'In-memory cache', 'cache redis elasticache memcached'],
    [shape('mxgraph.aws4.bucket', C.data, 'verticalLabelPosition=bottom;verticalAlign=top;'),
      78, 78, 'Object Store',
      'S3 / blob storage', 's3 bucket object storage blob'],
    [box(C.data), 140, 50, 'Data Lake',
      'Analytics storage layer', 'lake warehouse athena glue parquet'],

    // async
    [box(C.async, 'arcSize=10;'), 130, 45, 'Queue',
      'Point-to-point queue', 'queue sqs rabbit kafka buffer'],
    [box(C.async, 'arcSize=10;dashed=1;'), 130, 45, 'Topic',
      'Pub/sub topic', 'topic sns pubsub events eventbridge'],
    [box(C.async), 140, 50, 'Stream',
      'Append-only event stream', 'stream kinesis kafka log events'],

    // ai
    [box(C.ai, 'arcSize=30;'), 140, 55, 'LLM',
      'Model endpoint', 'llm model claude bedrock inference'],
    [box(C.ai), 150, 60, 'Agent',
      'Tool-using agent loop', 'agent mcp tools loop orchestrator'],
    [shape('cylinder3', C.ai, 'boundedLbl=1;backgroundOutline=1;size=12;'), 110, 80, 'Vector DB',
      'Embedding store for RAG', 'vector embedding rag pgvector opensearch'],
    [box(C.ai, 'dashed=1;'), 140, 50, 'MCP Server',
      'Model Context Protocol server', 'mcp tool server'],

    // ops
    [box(C.ops), 140, 50, 'Metrics',
      'Prometheus / CloudWatch', 'metrics prometheus cloudwatch grafana'],
    [box(C.ops), 140, 50, 'Logs',
      'Log pipeline', 'logs loki fluentbit cloudwatch'],
    [box(C.ops), 140, 50, 'Traces',
      'Distributed tracing', 'traces otel tempo xray jaeger'],
    [box(C.ops), 150, 50, 'CI/CD',
      'Pipeline / GitOps controller', 'ci cd argo flux github actions gitops'],
    [box(C.ops), 140, 50, 'Secrets',
      'Secret manager / vault', 'secrets vault ssm kms'],

    // boundaries
    [box(C.zone, 'container=1;collapsible=0;verticalAlign=top;align=left;spacingLeft=10;' +
      'spacingTop=6;dashed=1;dashPattern=6 4;fontColor=#5A5A66;fontStyle=1;'), 360, 240, 'VPC',
      'Network boundary', 'vpc network subnet boundary zone'],
    [box(C.zone, 'container=1;collapsible=0;verticalAlign=top;align=left;spacingLeft=10;' +
      'spacingTop=6;dashed=1;dashPattern=2 4;strokeColor=#C0392B;fontColor=#C0392B;fontStyle=1;'),
      360, 240, 'Trust Boundary',
      'Where the threat model changes', 'trust boundary security threat model zero trust'],
    [box(C.zone, 'container=1;collapsible=0;verticalAlign=top;align=left;spacingLeft=10;' +
      'spacingTop=6;fontColor=#5A5A66;fontStyle=1;'), 360, 240, 'Cluster',
      'Kubernetes cluster / account', 'cluster eks account region namespace']
  ];

  // [style, label, tooltip, search tags]
  var edges = [
    ['edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#2F5BB7;strokeWidth=1.5;' +
      'endArrow=blockThin;endFill=1;fontSize=11;', 'sync', 'Synchronous call',
      'sync request http grpc call'],
    ['edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#7B3FA0;strokeWidth=1.5;' +
      'dashed=1;endArrow=openThin;fontSize=11;', 'async', 'Async / event',
      'async event publish subscribe message'],
    ['edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#2E7D4F;strokeWidth=1.5;' +
      'endArrow=blockThin;endFill=1;startArrow=blockThin;startFill=1;fontSize=11;', 'mTLS',
      'Mutually authenticated link', 'mtls tls bidirectional secure'],
    ['edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#5A5A66;strokeWidth=1.2;' +
      'dashed=1;dashPattern=1 3;endArrow=openThin;fontSize=11;', 'telemetry',
      'Metrics / logs / traces flow', 'telemetry observability scrape export']
  ];

  var fns = [];

  vertices.forEach(function (v) {
    fns.push(sb.createVertexTemplateEntry(v[0], v[1], v[2], v[3], v[4], null, null, v[5]));
  });

  edges.forEach(function (e) {
    fns.push(sb.createEdgeTemplateEntry(e[0], 160, 0, e[1], e[2], null, e[3]));
  });

  sb.addPalette('notesArch', 'Notes / Architecture', true, function (content) {
    fns.forEach(function (fn) {
      content.appendChild(fn(content));
    });
  });

  // Move the palette above the stock ones so it is the first thing in the sidebar.
  try {
    var c = sb.container;
    var body = c.lastChild;
    var title = body.previousSibling;
    c.insertBefore(body, c.firstChild);
    c.insertBefore(title, body);
  } catch (e) {
    // Sidebar internals changed - the palette still works, just not pinned to the top.
  }

  // --- defaults for shapes drawn by hand ----------------------------------
  graph.currentVertexStyle = mxUtils.clone(graph.currentVertexStyle || {});
  graph.currentVertexStyle['rounded'] = '1';
  graph.currentVertexStyle['arcSize'] = '8';
  graph.currentVertexStyle['html'] = '1';
  graph.currentVertexStyle['whiteSpace'] = 'wrap';
  graph.currentVertexStyle['fontSize'] = '12';
  graph.currentVertexStyle['fontColor'] = '#1A1A1A';
  graph.currentVertexStyle['strokeWidth'] = '1.5';
  graph.currentVertexStyle['fillColor'] = C.compute.fill;
  graph.currentVertexStyle['strokeColor'] = C.compute.stroke;

  graph.currentEdgeStyle = mxUtils.clone(graph.currentEdgeStyle || {});
  graph.currentEdgeStyle['edgeStyle'] = 'orthogonalEdgeStyle';
  graph.currentEdgeStyle['rounded'] = '1';
  graph.currentEdgeStyle['html'] = '1';
  graph.currentEdgeStyle['fontSize'] = '11';
  graph.currentEdgeStyle['strokeWidth'] = '1.5';
  graph.currentEdgeStyle['strokeColor'] = C.edge.stroke;
  graph.currentEdgeStyle['endArrow'] = 'blockThin';
  graph.currentEdgeStyle['endFill'] = '1';
});
