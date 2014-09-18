<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF
   xmlns:cito="http://purl.org/spar/cito/"
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:dcterms="http://purl.org/dc/terms/"
   xmlns:foaf="http://xmlns.com/foaf/0.1/"
   xmlns:ore="http://www.openarchives.org/ore/terms/"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:rdfs1="http://www.w3.org/2001/01/rdf-schema#"
>
  <rdf:Description rdf:about="http://www.openarchives.org/ore/terms/Aggregation">
    <rdfs1:label>Aggregation</rdfs1:label>
    <rdfs1:isDefinedBy rdf:resource="http://www.openarchives.org/ore/terms/"/>
  </rdf:Description>
  <rdf:Description rdf:about="https://cn.dataone.org/cn/v1/resolve/${package_obsolete_uuid}">
    <rdf:type rdf:resource="http://www.openarchives.org/ore/terms/ResourceMap"/>
    <dcterms:modified>${package_modified}</dcterms:modified>
    <dcterms:creator rdf:resource="http://foresite-toolkit.googlecode.com/#pythonAgent"/>
    <dc:format>application/rdf+xml</dc:format>
    <ore:describes rdf:resource="https://cn.dataone.org/cn/v1/resolve/${package_obsolete_uuid}#aggregation"/>
    <dcterms:created>${package_created}</dcterms:created>
    <dcterms:identifier>${package_obsolete_uuid}</dcterms:identifier>
  </rdf:Description>
  <rdf:Description rdf:about="https://cn.dataone.org/cn/v1/resolve/${data_obsolete_uuid}">
    <cito:isDocumentedBy rdf:resource="https://cn.dataone.org/cn/v1/resolve/${metadata_obsolete_uuid}"></cito:isDocumentedBy>
    <dcterms:description>Data object ("${data_obsolete_uuid}")</dcterms:description>
    <dcterms:identifier>${data_obsolete_uuid}</dcterms:identifier>
    <dc:title>Dataset: "${data_obsolete_uuid}"</dc:title>
  </rdf:Description>
  <rdf:Description rdf:about="https://cn.dataone.org/cn/v1/resolve/${metadata_obsolete_uuid}">
    <cito:documents rdf:resource="https://cn.dataone.org/cn/v1/resolve/${data_obsolete_uuid}"></cito:documents>
    <dcterms:description>Science metadata object (${metadata_obsolete_uuid}) for Data object ("${data_obsolete_uuid}")</dcterms:description>
    <dcterms:identifier>${metadata_obsolete_uuid}</dcterms:identifier>
    <dc:title>Metadata: ${metadata_obsolete_uuid}</dc:title>
  </rdf:Description>
  <rdf:Description rdf:about="http://www.openarchives.org/ore/terms/ResourceMap">
    <rdfs1:label>ResourceMap</rdfs1:label>
    <rdfs1:isDefinedBy rdf:resource="http://www.openarchives.org/ore/terms/"/>
  </rdf:Description>
  <rdf:Description rdf:about="https://cn.dataone.org/cn/v1/resolve/${package_obsolete_uuid}#aggregation">
    <rdf:type rdf:resource="http://www.openarchives.org/ore/terms/Aggregation"/>
    <ore:aggregates rdf:resource="https://cn.dataone.org/cn/v1/resolve/${metadata_obsolete_uuid}"/>
    <ore:aggregates rdf:resource="https://cn.dataone.org/cn/v1/resolve/${data_obsolete_uuid}"/>
    <ore:isDescribedBy rdf:resource="https://cn.dataone.org/cn/v1/resolve/${package_obsolete_uuid}"/>
  </rdf:Description>
  <rdf:Description rdf:about="http://foresite-toolkit.googlecode.com/#pythonAgent">
    <foaf:name>Foresite Toolkit (Python)</foaf:name>
    <foaf:mbox>foresite@googlegroups.com</foaf:mbox>
  </rdf:Description>
</rdf:RDF>

