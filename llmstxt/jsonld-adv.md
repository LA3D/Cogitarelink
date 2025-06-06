Advanced Concepts
This section is non-normative.

JSON-LD has a number of features that provide functionality above and beyond the core functionality described above. JSON can be used to express data using such structures, and the features described in this section can be used to interpret a variety of different JSON structures as Linked Data. A JSON-LD processor will make use of provided and embedded contexts to interpret property values in a number of different idiomatic ways.

Describing values

One pattern in JSON is for the value of a property to be a string. Often times, this string actually represents some other typed value, for example an IRI, a date, or a string in some specific language. See § 4.2 Describing Values for details on how to describe such value typing.

Value ordering

In JSON, a property with an array value implies an implicit order; arrays in JSON-LD do not convey any ordering of the contained elements by default, unless defined using embedded structures or through a context definition. See § 4.3 Value Ordering for a further discussion.

Property nesting

Another JSON idiom often found in APIs is to use an intermediate object to group together related properties of an object; in JSON-LD these are referred to as nested properties and are described in § 4.4 Nested Properties.

Referencing objects

Linked Data is all about describing the relationships between different resources. Sometimes these relationships are between resources defined in different documents described on the web, sometimes the resources are described within the same document.

EXAMPLE 17: Referencing Objects on the Web Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@vocab": "http://xmlns.com/foaf/0.1/", "knows": {"@type": "@id"} }, "@id": "http://manu.sporny.org/about#manu", "@type": "Person", "name": "Manu Sporny", "knows": "https://greggkellogg.net/foaf#me" }

In this case, a document residing at http://manu.sporny.org/about may contain the example above, and reference another document at https://greggkellogg.net/foaf which could include a similar representation.

A common idiom found in JSON usage is objects being specified as the value of other objects, called object embedding in JSON-LD; for example, a friend specified as an object value of a Person:

EXAMPLE 18: Embedding Objects Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@vocab": "http://xmlns.com/foaf/0.1/" }, "@id": "http://manu.sporny.org/about#manu", "@type": "Person", "name": "Manu Sporny", "knows": { "@id": "https://greggkellogg.net/foaf#me", "@type": "Person", "name": "Gregg Kellogg" } }

See § 4.5 Embedding details these relationships.

Indexed values

Another common idiom in JSON is to use an intermediate object to represent property values via indexing. JSON-LD allows data to be indexed in a number of different ways, as detailed in § 4.6 Indexed Values.

Reverse Properties

JSON-LD serializes directed graphs. That means that every property points from a node to another node or value. However, in some cases, it is desirable to serialize in the reverse direction, as detailed in § 4.8 Reverse Properties.

The following sections describe such advanced functionality in more detail.

4.1 Advanced Context Usage

This section is non-normative.

Section § 3.1 The Context introduced the basics of what makes JSON-LD work. This section expands on the basic principles of the context and demonstrates how more advanced use cases can be achieved using JSON-LD.

In general, contexts may be used any time a map is defined. The only time that one cannot express a context is as a direct child of another context definition (other than as part of an expanded term definition). For example, a JSON-LD document may have the form of an array composed of one or more node objects, which use a context definition in each top-level node object:

EXAMPLE 19: Using multiple contexts Compacted (Input) Expanded (Result) Statements Turtle Open in playground [ { "@context": "https://json-ld.org/contexts/person.jsonld", "name": "Manu Sporny", "homepage": "http://manu.sporny.org/", "depiction": "http://twitter.com/account/profile_image/manusporny" }, { "@context": "https://json-ld.org/contexts/place.jsonld", "name": "The Empire State Building", "description": "The Empire State Building is a 102-story landmark in New York City.", "geo": { "latitude": "40.75", "longitude": "73.98" } } ]

The outer array is standard for a document in expanded document form and flattened document form, and may be necessary when describing a disconnected graph, where nodes may not reference each other. In such cases, using a top-level map with a @graph property can be useful for saving the repetition of @context. See § 4.5 Embedding for more.

EXAMPLE 20: Describing disconnected nodes with @graph Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": [ "https://json-ld.org/contexts/person.jsonld", "https://json-ld.org/contexts/place.jsonld", {"title": "http://purl.org/dc/terms/title"} ], "@graph": [{ "http://xmlns.com/foaf/0.1/name": "Manu Sporny", "homepage": "http://manu.sporny.org/", "depiction": "http://twitter.com/account/profile_image/manusporny" }, { "title": "The Empire State Building", "description": "The Empire State Building is a 102-story landmark in New York City.", "geo": { "latitude": "40.75", "longitude": "73.98" } }] }

Duplicate context terms are overridden using a most-recently-defined-wins mechanism.

EXAMPLE 21: Embedded contexts within node objects Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "name": "http://example.com/person#name", "details": "http://example.com/person#details" }, "name": "Markus Lanthaler", ... "details": { "@context": { "name": "http://example.com/organization#name" }, "name": "Graz University of Technology" } }

In the example above, the name term is overridden in the more deeply nested details structure, which uses its own embedded context. Note that this is rarely a good authoring practice and is typically used when working with legacy applications that depend on a specific structure of the map. If a term is redefined within a context, all previous rules associated with the previous definition are removed. If a term is redefined to null, the term is effectively removed from the list of terms defined in the active context.

Multiple contexts may be combined using an array, which is processed in order. The set of contexts defined within a specific map are referred to as local contexts. The active context refers to the accumulation of local contexts that are in scope at a specific point within the document. Setting a local context to null effectively resets the active context to an empty context, without term definitions, default language, or other things defined within previous contexts. The following example specifies an external context and then layers an embedded context on top of the external context:

In JSON-LD 1.1, there are other mechanisms for introducing contexts, including scoped contexts and imported contexts, and there are new ways of protecting term definitions, so there are cases where the last defined inline context is not necessarily one which defines the scope of terms. See § 4.1.8 Scoped Contexts, § 4.1.9 Context Propagation, § 4.1.10 Imported Contexts, and § 4.1.11 Protected Term Definitions for further information.

EXAMPLE 22: Combining external and local contexts Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": [ "https://json-ld.org/contexts/person.jsonld", { "pic": { "@id": "http://xmlns.com/foaf/0.1/depiction", "@type": "@id" } } ], "name": "Manu Sporny", "homepage": "http://manu.sporny.org/", "pic": "http://twitter.com/account/profile_image/manusporny" } NOTE

When possible, the context definition should be put at the top of a JSON-LD document. This makes the document easier to read and might make streaming parsers more efficient. Documents that do not have the context at the top are still conformant JSON-LD.

NOTE

To avoid forward-compatibility issues, terms starting with an @ character followed exclusively by one or more ALPHA characters (see [RFC5234]) are to be avoided as they might be used as keyword in future versions of JSON-LD. Terms starting with an @ character that are not JSON-LD 1.1 keywords are treated as any other term, i.e., they are ignored unless mapped to an IRI. Furthermore, the use of empty terms ("") is not allowed as not all programming languages are able to handle empty JSON keys.

4.1.1 JSON-LD 1.1 Processing Mode

This section is non-normative.

New features defined in JSON-LD 1.1 are available unless the processing mode is set to json-ld-1.0. This may be set through an API option. The processing mode may be explicitly set to json-ld-1.1 using the @version entry in a context set to the value 1.1 as a number, or through an API option. Explicitly setting the processing mode to json-ld-1.1 will prohibit JSON-LD 1.0 processors from incorrectly processing a JSON-LD 1.1 document.

EXAMPLE 23: Setting @version in context { "@context": { "@version": 1.1, ... }, ... }

The first context encountered when processing a document which contains @version determines the processing mode, unless it is defined explicitly through an API option. This means that if "@version": 1.1 is encountered after processing a context without @version, the former will be interpreted as having had "@version": 1.1 defined within it.

NOTE

Setting the processing mode explicitly to json-ld-1.1 is RECOMMENDED to prevent a JSON-LD 1.0 processor from incorrectly processing a JSON-LD 1.1 document and producing different results.

4.1.2 Default Vocabulary

This section is non-normative.

At times, all properties and types may come from the same vocabulary. JSON-LD's @vocab keyword allows an author to set a common prefix which is used as the vocabulary mapping and is used for all properties and types that do not match a term and are neither an IRI nor a compact IRI (i.e., they do not contain a colon).

EXAMPLE 24: Using a default vocabulary Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@vocab": "http://example.com/vocab/" }, "@id": "http://example.org/places#BrewEats", "@type": "Restaurant", "name": "Brew Eats" ... }

If @vocab is used but certain keys in an map should not be expanded using the vocabulary IRI, a term can be explicitly set to null in the context. For instance, in the example below the databaseId entry would not expand to an IRI causing the property to be dropped when expanding.

EXAMPLE 25: Using the null keyword to ignore data Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@vocab": "http://example.com/vocab/", "databaseId": null }, "@id": "http://example.org/places#BrewEats", "@type": "Restaurant", "name": "Brew Eats", "databaseId": "23987520" }

Since JSON-LD 1.1, the vocabulary mapping in a local context can be set to a relative IRI reference, which is concatenated to any vocabulary mapping in the active context (see § 4.1.4 Using the Document Base for the Default Vocabulary for how this applies if there is no vocabulary mapping in the active context).

The following example illustrates the affect of expanding a property using a relative IRI reference, which is shown in the Expanded (Result) tab below.

EXAMPLE 26: Using a default vocabulary relative to a previous default vocabulary Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": [{ "@vocab": "http://example.com/" }, { "@version": 1.1, "@vocab": "vocab/" }], "@id": "http://example.org/places#BrewEats", "@type": "Restaurant", "name": "Brew Eats" ... } NOTE

The grammar for @vocab, as defined in § 9.15 Context Definitions allows the value to be a term or compact IRI. Note that terms used in the value of @vocab must be in scope at the time the context is introduced, otherwise there would be a circular dependency between @vocab and other terms defined in the same context.

4.1.3 Base IRI

This section is non-normative.

JSON-LD allows IRIs to be specified in a relative form which is resolved against the document base according section 5.1 Establishing a Base URI of [RFC3986]. The base IRI may be explicitly set with a context using the @base keyword.

For example, if a JSON-LD document was retrieved from http://example.com/document.jsonld, relative IRI references would resolve against that IRI:

EXAMPLE 27: Use a relative IRI reference as node identifier { "@context": { "label": "http://www.w3.org/2000/01/rdf-schema#label" }, "@id": "", "label": "Just a simple document" }

This document uses an empty @id, which resolves to the document base. However, if the document is moved to a different location, the IRI would change. To prevent this without having to use an IRI, a context may define an @base mapping, to overwrite the base IRI for the document.

EXAMPLE 28: Setting the document base in a document Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@base": "http://example.com/document.jsonld", "label": "http://www.w3.org/2000/01/rdf-schema#label" }, "@id": "", "label": "Just a simple document" }

Setting @base to null will prevent relative IRI references from being expanded to IRIs.

Please note that the @base will be ignored if used in external contexts.

4.1.4 Using the Document Base for the Default Vocabulary

This section is non-normative.

In some cases, vocabulary terms are defined directly within the document itself, rather than in an external vocabulary. Since JSON-LD 1.1, the vocabulary mapping in a local context can be set to a relative IRI reference, which is, if there is no vocabulary mapping in scope, resolved against the base IRI. This causes terms which are expanded relative to the vocabulary, such as the keys of node objects, to be based on the base IRI to create IRIs.

EXAMPLE 29: Using "#" as the vocabulary mapping { "@context": { "@version": 1.1, "@base": "http://example/document", "@vocab": "#" }, "@id": "http://example.org/places#BrewEats", "@type": "Restaurant", "name": "Brew Eats" ... }

If this document were located at http://example/document, it would expand as follows:

EXAMPLE 30: Using "#" as the vocabulary mapping (expanded) Expanded (Result) Statements Turtle Open in playground [{ "@id": "http://example.org/places#BrewEats", "@type": ["http://example/document#Restaurant"], "http://example/document#name": [{"@value": "Brew Eats"}] }] 4.1.5 Compact IRIs

This section is non-normative.

A compact IRI is a way of expressing an IRI using a prefix and suffix separated by a colon (:). The prefix is a term taken from the active context and is a short string identifying a particular IRI in a JSON-LD document. For example, the prefix foaf may be used as a shorthand for the Friend-of-a-Friend vocabulary, which is identified using the IRI http://xmlns.com/foaf/0.1/. A developer may append any of the FOAF vocabulary terms to the end of the prefix to specify a short-hand version of the IRI for the vocabulary term. For example, foaf:name would be expanded to the IRI http://xmlns.com/foaf/0.1/name.

EXAMPLE 31: Prefix expansion Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "foaf": "http://xmlns.com/foaf/0.1/" ... }, "@type": "foaf:Person", "foaf:name": "Dave Longley", ... }

In the example above, foaf:name expands to the IRI http://xmlns.com/foaf/0.1/name and foaf:Person expands to http://xmlns.com/foaf/0.1/Person.

Prefixes are expanded when the form of the value is a compact IRI represented as a prefix:suffix combination, the prefix matches a term defined within the active context, and the suffix does not begin with two slashes (//). The compact IRI is expanded by concatenating the IRI mapped to the prefix to the (possibly empty) suffix. If the prefix is not defined in the active context, or the suffix begins with two slashes (such as in http://example.com), the value is interpreted as IRI instead. If the prefix is an underscore (_), the value is interpreted as blank node identifier instead.

It's also possible to use compact IRIs within the context as shown in the following example:

EXAMPLE 32: Using vocabularies Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "xsd": "http://www.w3.org/2001/XMLSchema#", "foaf": "http://xmlns.com/foaf/0.1/", "foaf:homepage": { "@type": "@id" }, "picture": { "@id": "foaf:depiction", "@type": "@id" } }, "@id": "http://me.markus-lanthaler.com/", "@type": "foaf:Person", "foaf:name": "Markus Lanthaler", "foaf:homepage": "http://www.markus-lanthaler.com/", "picture": "http://twitter.com/account/profile_image/markuslanthaler" }

When operating explicitly with the processing mode for JSON-LD 1.0 compatibility, terms may be chosen as compact IRI prefixes when compacting only if a simple term definition is used where the value ends with a URI gen-delim character (e.g, /, # and others, see [RFC3986]).

In JSON-LD 1.1, terms may be chosen as compact IRI prefixes when expanding or compacting only if a simple term definition is used where the value ends with a URI gen-delim character, or if their expanded term definition contains a @prefix entry with the value true. If a simple term definition does not end with a URI gen-delim character, or a expanded term definition contains a @prefix entry with the value false, the term will not be used for either expanding compact IRIs or compacting IRIs to compact IRIs.

NOTE

The term selection behavior for 1.0 processors was changed as a result of an errata against JSON-LD 1.0 reported here. This does not affect the behavior of processing existing JSON-LD documents, but creates a slight change when compacting documents using Compact IRIs.

The behavior when compacting can be illustrated by considering the following input document in expanded form:

EXAMPLE 33: Expanded document used to illustrate compact IRI creation [{ "http://example.com/vocab/property": [{"@value": "property"}], "http://example.com/vocab/propertyOne": [{"@value": "propertyOne"}] }]

Using the following context in the 1.0 processing mode will now select the term vocab rather than property, even though the IRI associated with property captures more of the original IRI.

EXAMPLE 34: Compact IRI generation context (1.0) { "@context": { "vocab": "http://example.com/vocab/", "property": "http://example.com/vocab/property" } }

Compacting using the previous context with the above expanded input document results in the following compacted result:

EXAMPLE 35: Compact IRI generation term selection (1.0) Compacted (Result) Statements Turtle Open in playground { "@context": { "vocab": "http://example.com/vocab/", "property": "http://example.com/vocab/property" }, "property": "property", "vocab:propertyOne": "propertyOne" }

In the original [JSON-LD10], the term selection algorithm would have selected property, creating the Compact IRI property:One. The original behavior can be made explicit using @prefix:

EXAMPLE 36: Compact IRI generation context (1.1) { "@context": { "@version": 1.1, "vocab": "http://example.com/vocab/", "property": { "@id": "http://example.com/vocab/property", "@prefix": true } } } EXAMPLE 37: Compact IRI generation term selection (1.1) Compacted (Input) Statements Turtle Open in playground { "@context": { "@version": 1.1, "vocab": "http://example.com/vocab/", "property": { "@id": "http://example.com/vocab/property", "@prefix": true } }, "property": "property", "property:One": "propertyOne" }

In this case, the property term would not normally be usable as a prefix, both because it is defined with an expanded term definition, and because its @id does not end in a gen-delim character. Adding "@prefix": true allows it to be used as the prefix portion of the compact IRI property:One.

4.1.6 Aliasing Keywords

This section is non-normative.

Each of the JSON-LD keywords, except for @context, may be aliased to application-specific keywords. This feature allows legacy JSON content to be utilized by JSON-LD by re-using JSON keys that already exist in legacy documents. This feature also allows developers to design domain-specific implementations using only the JSON-LD context.

EXAMPLE 38: Aliasing keywords Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "url": "@id", "a": "@type", "name": "http://xmlns.com/foaf/0.1/name" }, "url": "http://example.com/about#gregg", "a": "http://xmlns.com/foaf/0.1/Person", "name": "Gregg Kellogg" }

In the example above, the @id and @type keywords have been given the aliases url and a, respectively.

Other than for @type, properties of expanded term definitions where the term is a keyword result in an error. Unless the processing mode is set to json-ld-1.0, there is also an exception for @type; see § 4.3.3 Using @set with @type for further details and usage examples.

Unless the processing mode is set to json-ld-1.0, aliases of keywords are either simple term definitions, where the value is a keyword, or a expanded term definitions with an @id entry and optionally an @protected entry; no other entries are allowed. There is also an exception for aliases of @type, as indicated above. See § 4.1.11 Protected Term Definitions for further details of using @protected.

Since keywords cannot be redefined, they can also not be aliased to other keywords.

NOTE

Aliased keywords may not be used within a context, itself.

See § 9.16 Keywords for a normative definition of all keywords.

4.1.7 IRI Expansion within a Context

This section is non-normative.

In general, normal IRI expansion rules apply anywhere an IRI is expected (see § 3.2 IRIs). Within a context definition, this can mean that terms defined within the context may also be used within that context as long as there are no circular dependencies. For example, it is common to use the xsd namespace when defining typed values:

EXAMPLE 39: IRI expansion within a context { "@context": { "xsd": "http://www.w3.org/2001/XMLSchema#", "name": "http://xmlns.com/foaf/0.1/name", "age": { "@id": "http://xmlns.com/foaf/0.1/age", "@type": "xsd:integer" }, "homepage": { "@id": "http://xmlns.com/foaf/0.1/homepage", "@type": "@id" } }, ... }

In this example, the xsd term is defined and used as a prefix for the @type coercion of the age property.

Terms may also be used when defining the IRI of another term:

EXAMPLE 40: Using a term to define the IRI of another term within a context { "@context": { "foaf": "http://xmlns.com/foaf/0.1/", "xsd": "http://www.w3.org/2001/XMLSchema#", "name": "foaf:name", "age": { "@id": "foaf:age", "@type": "xsd:integer" }, "homepage": { "@id": "foaf:homepage", "@type": "@id" } }, ... }

Compact IRIs and IRIs may be used on the left-hand side of a term definition.

EXAMPLE 41: Using a compact IRI as a term { "@context": { "foaf": "http://xmlns.com/foaf/0.1/", "xsd": "http://www.w3.org/2001/XMLSchema#", "name": "foaf:name", "foaf:age": { "@id": "http://xmlns.com/foaf/0.1/age", "@type": "xsd:integer" }, "foaf:homepage": { "@type": "@id" } }, ... }

In this example, the compact IRI form is used in two different ways. In the first approach, foaf:age declares both the IRI for the term (using short-form) as well as the @type associated with the term. In the second approach, only the @type associated with the term is specified. The full IRI for foaf:homepage is determined by looking up the foaf prefix in the context.

Warning

If a compact IRI is used as a term, it must expand to the value that compact IRI would have on its own when expanded. This represents a change to the original 1.0 algorithm to prevent terms from expanding to a different IRI, which could lead to undesired results.

EXAMPLE 42: Illegal Aliasing of a compact IRI to a different IRI { "@context": { "foaf": "http://xmlns.com/foaf/0.1/", "xsd": "http://www.w3.org/2001/XMLSchema#", "name": "foaf:name", "foaf:age": { "@id": "http://xmlns.com/foaf/0.1/age", "@type": "xsd:integer" }, "foaf:homepage": { "@id": "http://schema.org/url", "@type": "@id" } }, ... }

IRIs may also be used in the key position in a context:

EXAMPLE 43: Associating context definitions with IRIs { "@context": { "foaf": "http://xmlns.com/foaf/0.1/", "xsd": "http://www.w3.org/2001/XMLSchema#", "name": "foaf:name", "foaf:age": { "@id": "http://xmlns.com/foaf/0.1/age", "@type": "xsd:integer" }, "http://xmlns.com/foaf/0.1/homepage": { "@type": "@id" } }, ... }

In order for the IRI to match above, the IRI needs to be used in the JSON-LD document. Also note that foaf:homepage will not use the { "@type": "@id" } declaration because foaf:homepage is not the same as http://xmlns.com/foaf/0.1/homepage. That is, terms are looked up in a context using direct string comparison before the prefix lookup mechanism is applied.

Warning

Neither an IRI reference nor a compact IRI may expand to some other unrelated IRI. This represents a change to the original 1.0 algorithm which allowed this behavior but discouraged it.

The only other exception for using terms in the context is that circular definitions are not allowed. That is, a definition of term1 cannot depend on the definition of term2 if term2 also depends on term1. For example, the following context definition is illegal:

EXAMPLE 44: Illegal circular definition of terms within a context { "@context": { "term1": "term2:foo", "term2": "term1:bar" }, ... } 4.1.8 Scoped Contexts

This section is non-normative.

An expanded term definition can include a @context property, which defines a context (a scoped context) for values of properties defined using that term. When used for a property, this is called a property-scoped context. This allows values to use term definitions, the base IRI, vocabulary mappings or the default language which are different from the node object they are contained in, as if the context was specified within the value itself.

EXAMPLE 45: Defining an @context within a term definition Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "name": "http://schema.org/name", "interest": { "@id": "http://xmlns.com/foaf/0.1/interest", "@context": {"@vocab": "http://xmlns.com/foaf/0.1/"} } }, "name": "Manu Sporny", "interest": { "@id": "https://www.w3.org/TR/json-ld11/", "name": "JSON-LD", "topic": "Linking Data" } }

In this case, the social profile is defined using the schema.org vocabulary, but interest is imported from FOAF, and is used to define a node describing one of Manu's interests where those properties now come from the FOAF vocabulary.

Expanding this document, uses a combination of terms defined in the outer context, and those defined specifically for that term in a property-scoped context.

Scoping can also be performed using a term used as a value of @type:

EXAMPLE 46: Defining an @context within a term definition used on @type Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "name": "http://schema.org/name", "interest": "http://xmlns.com/foaf/0.1/interest", "Person": "http://schema.org/Person", "Document": { "@id": "http://xmlns.com/foaf/0.1/Document", "@context": {"@vocab": "http://xmlns.com/foaf/0.1/"} } }, "@type": "Person", "name": "Manu Sporny", "interest": { "@id": "https://www.w3.org/TR/json-ld11/", "@type": "Document", "name": "JSON-LD", "topic": "Linking Data" } }

Scoping on @type is useful when common properties are used to relate things of different types, where the vocabularies in use within different entities calls for different context scoping. For example, hasPart/partOf may be common terms used in a document, but mean different things depending on the context. A type-scoped context is only in effect for the node object on which the type is used; the previous in-scope contexts are placed back into effect when traversing into another node object. As described further in § 4.1.9 Context Propagation, this may be controlled using the @propagate keyword.

NOTE

Any property-scoped or local contexts that were introduced in the node object would still be in effect when traversing into another node object.

When expanding, each value of @type is considered (ordering them lexicographically) where that value is also a term in the active context having its own type-scoped context. If so, that the scoped context is applied to the active context.

NOTE

The values of @type are unordered, so if multiple types are listed, the order that type-scoped contexts are applied is based on lexicographical ordering.

For example, consider the following semantically equivalent examples. The first example, shows how properties and types can define their own scoped contexts, which are included when expanding.

EXAMPLE 47: Expansion using embedded and scoped contexts { "@context": { "@version": 1.1, "@vocab": "http://example.com/vocab/", "property": { "@id": "http://example.com/vocab/property", "@context": { "term1": "http://example.com/vocab/term1" ↑ Scoped context for "property" defines term1 } }, "Type1": { "@id": "http://example.com/vocab/Type1", "@context": { "term3": "http://example.com/vocab/term3" ↑ Scoped context for "Type1" defines term3 } }, "Type2": { "@id": "http://example.com/vocab/Type2", "@context": { "term4": "http://example.com/vocab/term4" ↑ Scoped context for "Type2" defines term4 } } }, "property": { "@context": { "term2": "http://example.com/vocab/term2" ↑ Embedded context defines term2 }, "@type": ["Type2", "Type1"], "term1": "a", "term2": "b", "term3": "c", "term4": "d" } }

Contexts are processed depending on how they are defined. A property-scoped context is processed first, followed by any embedded context, followed lastly by the type-scoped contexts, in the appropriate order. The previous example is logically equivalent to the following:

EXAMPLE 48: Expansion using embedded and scoped contexts (embedding equivalent) { "@context": { "@vocab": "http://example.com/vocab/", "property": "http://example.com/vocab/property", "Type1": "http://example.com/vocab/Type1", "Type2": "http://example.com/vocab/Type2" }, "property": { "@context": [{ "term1": "http://example.com/vocab/term1" ↑ Previously scoped context for "property" defines term1 }, { "term2": "http://example.com/vocab/term2" ↑ Embedded context defines term2 }, { "term3": "http://example.com/vocab/term3" ↑ Previously scoped context for "Type1" defines term3 }, { "term4": "http://example.com/vocab/term4" ↑ Previously scoped context for "Type2" defines term4 }], "@type": ["Type2", "Type1"], "term1": "a", "term2": "b", "term3": "c", "term4": "d" } } NOTE

If a term defines a scoped context, and then that term is later redefined, the association of the context defined in the earlier expanded term definition is lost within the scope of that redefinition. This is consistent with term definitions of a term overriding previous term definitions from earlier less deeply nested definitions, as discussed in § 4.1 Advanced Context Usage.

NOTE

Scoped Contexts are a new feature in JSON-LD 1.1.

4.1.9 Context Propagation

This section is non-normative.

Once introduced, contexts remain in effect until a subsequent context removes it by setting @context to null, or by redefining terms, with the exception of type-scoped contexts, which limit the effect of that context until the next node object is entered. This behavior can be changed using the @propagate keyword.

The following example illustrates how terms defined in a context with @propagate set to false are effectively removed when descending into new node object.

EXAMPLE 49: Marking a context to not propagate Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "term": { "@id": "http://example.org/original", "@context": { "@propagate": false, ↑ Scoped context only lasts in one node-object "term": "http://example.org/non-propagated-term" } } }, "term": { ↑ This term is the original "term": { ↑ This term is from the scoped context "term": "This term is from the first context" ↑ This term is the original again } } } NOTE

Contexts included within an array must all have the same value for @propagate due to the way that rollback is defined in JSON-LD 1.1 Processing Algorithms and API.

4.1.10 Imported Contexts

This section is non-normative.

JSON-LD 1.0 included mechanisms for modifying the context that is in effect. This included the capability to load and process a remote context and then apply further changes to it via new contexts.

However, with the introduction of JSON-LD 1.1, it is also desirable to be able to load a remote context, in particular an existing JSON-LD 1.0 context, and apply JSON-LD 1.1 features to it prior to processing.

By using the @import keyword in a context, another remote context, referred to as an imported context, can be loaded and modified prior to processing. The modifications are expressed in the context that includes the @import keyword, referred to as the wrapping context. Once an imported context is loaded, the contents of the wrapping context are merged into it prior to processing. The merge operation will cause each key-value pair in the wrapping context to be added to the loaded imported context, with the wrapping context key-value pairs taking precedence.

By enabling existing contexts to be reused and edited inline prior to processing, context-wide keywords can be applied to adjust all term definitions in the imported context. Similarly, term definitions can be replaced prior to processing, enabling adjustments that, for instance, ensure term definitions match previously protected terms or that they include additional type coercion information.

The following examples illustrate how @import can be used to express a type-scoped context that loads an imported context and sets @propagate to true, as a technique for making other similar modifications.

Suppose there was a context that could be referenced remotely via the URL https://json-ld.org/contexts/remote-context.jsonld:

EXAMPLE 50: A remote context to be imported in a type-scoped context { "@context": { "Type1": "http://example.com/vocab/Type1", "Type2": "http://example.com/vocab/Type2", "term1": "http://example.com/vocab#term1", "term2": "http://example.com/vocab#term2", ... } }

A wrapping context could be used to source it and modify it:

EXAMPLE 51: Sourcing a context in a type-scoped context and setting it to propagate { "@context": { "@version": 1.1, "MyType": { "@id": "http://example.com/vocab#MyType", "@context": { "@version": 1.1, "@import": "https://json-ld.org/contexts/remote-context.jsonld", "@propagate": true } } } }

The effect would be the same as if the entire imported context had been copied into the type-scoped context:

EXAMPLE 52: Result of sourcing a context in a type-scoped context and setting it to propagate { "@context": { "@version": 1.1, "MyType": { "@id": "http://example.com/vocab#MyType", "@context": { "@version": 1.1, "Type1": "http://example.com/vocab/Type1", "Type2": "http://example.com/vocab/Type2", "term1": "http://example.com/vocab#term1", "term2": "http://example.com/vocab#term2", ... "@propagate": true } } } }

Similarly, the wrapping context may replace term definitions or set other context-wide keywords that may affect how the imported context term definitions will be processed:

EXAMPLE 53: Sourcing a context to modify @vocab and a term definition { "@context": { "@version": 1.1, "@import": "https://json-ld.org/contexts/remote-context.jsonld", "@vocab": "http://example.org/vocab#", ↑ This will replace any previous @vocab definition prior to processing it "term1": { "@id": "http://example.org/vocab#term1", "@type": "http://www.w3.org/2001/XMLSchema#integer" } ↑ This will replace the old term1 definition prior to processing it } }

Again, the effect would be the same as if the entire imported context had been copied into the context:

EXAMPLE 54: Result of sourcing a context to modify @vocab and a term definition { "@context": { "@version": 1.1, "Type1": "http://example.com/vocab/Type1", "Type2": "http://example.com/vocab/Type2", "term1": { "@id": "http://example.org/vocab#term1", "@type": "http://www.w3.org/2001/XMLSchema#integer" }, ↑ Note term1 has been replaced prior to processing "term2": "http://example.com/vocab#term2", ..., "@vocab": "http://example.org/vocab#" } }

The result of loading imported contexts must be context definition, not an IRI or an array. Additionally, the imported context cannot include an @import entry.

4.1.11 Protected Term Definitions

This section is non-normative.

JSON-LD is used in many specifications as the specified data format. However, there is also a desire to allow some JSON-LD contents to be processed as plain JSON, without using any of the JSON-LD algorithms. Because JSON-LD is very flexible, some terms from the original format may be locally overridden through the use of embedded contexts, and take a different meaning for JSON-LD based implementations. On the other hand, "plain JSON" implementations may not be able to interpret these embedded contexts, and hence will still interpret those terms with their original meaning. To prevent this divergence of interpretation, JSON-LD 1.1 allows term definitions to be protected.

A protected term definition is a term definition with an entry @protected set to true. It generally prevents further contexts from overriding this term definition, either through a new definition of the same term, or through clearing the context with "@context": null. Such attempts will raise an error and abort the processing (except in some specific situations described below).

EXAMPLE 55: A protected term definition can generally not be overridden { "@context": [ { "@version": 1.1, "Person": "http://xmlns.com/foaf/0.1/Person", "knows": "http://xmlns.com/foaf/0.1/knows", "name": { "@id": "http://xmlns.com/foaf/0.1/name", "@protected": true } }, { – this attempt will fail with an error "name": "http://schema.org/name" } ], "@type": "Person", "name": "Manu Sporny", "knows": { "@context": [ – this attempt would also fail with an error null, "http://schema.org/" ], "name": "Gregg Kellogg" } }

When all or most term definitions of a context need to be protected, it is possible to add an entry @protected set to true to the context itself. It has the same effect as protecting each of its term definitions individually. Exceptions can be made by adding an entry @protected set to false in some term definitions.

EXAMPLE 56: A protected @context with an exception Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": [ { "@version": 1.1, "@protected": true, "name": "http://schema.org/name", "member": "http://schema.org/member", "Person": { "@id": "http://schema.org/Person", "@protected": false } } ], "name": "Digital Bazaar", "member": { "@context": { ­– name is protected, so the following would fail with an error – "name": "http://xmlns.com/foaf/0.1/Person", ­– Person is not protected, and can be overridden "Person": "http://xmlns.com/foaf/0.1/Person" }, "@type": "Person", "name": "Manu Sporny" } }

While protected terms can in general not be overridden, there are two exceptions to this rule. The first exception is that a context is allowed to redefine a protected term if the new definition is identical to the protected term definition (modulo the @protected flag). The rationale is that the new definition does not violate the protection, as it does not change the semantics of the protected term. This is useful for widespread term definitions, such as aliasing @type to type, which may occur (including in a protected form) in several contexts.

EXAMPLE 57: Overriding permitted if both definitions are identical Original Expanded Statements Turtle Open in playground { "@context": [ { "@version": 1.1, "@protected": true, "id": "@id", "type": "@type", "Organization": "http://example.org/orga/Organization", "member": { "@id": "http://example.org/orga/member", "@type": "@id" } }, { "id": "@id", "type": "@type", ­– Those "redefinitions" do not raise an error. ­– Note however that the terms are still protected "Person": "http://schema.org/Person", "name": "http://schema.org/name" } ], "id": "https://digitalbazaar.com/", "type": "Organization", "member" : { "id": "http://manu.sporny.org/about#manu", "type": "Person", "name": "Manu Sporny" } }

The second exception is that a property-scoped context is not affected by protection, and can therefore override protected terms, either with a new term definition, or by clearing the context with "@context": null.

The rationale is that "plain JSON" implementations, relying on a given specification, will only traverse properties defined by that specification. Scoped contexts belonging to the specified properties are part of the specification, so the "plain JSON" implementations are expected to be aware of the change of semantics they induce. Scoped contexts belonging to other properties apply to parts of the document that "plain JSON" implementations will ignore. In both cases, there is therefore no risk of diverging interpretations between JSON-LD-aware implementations and "plain JSON" implementations, so overriding is permitted.

EXAMPLE 58: overriding permitted in property scoped context Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": [ { – This context reflects the specification used by "plain JSON" implementations "@version": 1.1, "@protected": true, "Organization": "http://schema.org/Organization", "name": "http://schema.org/name", "employee": { "@id": "http://schema.org/employee", "@context": { "@protected": true, "name": "http://schema.org/familyName" } ↑ overrides the definition of "name" } }, { – This context extends the previous one, – only JSON-LD-aware implementations are expected to use it "location": { "@id": "http://xmlns.com/foaf/0.1/based_near", "@context": [ null, ↑ clears the context entirely, including all protected terms { "@vocab": "http://xmlns.com/foaf/0.1/" } ] } } ], "@type": "Organization", "name": "Digital Bazaar", "employee" : { "name": "Sporny", "location": {"name": "Blacksburg, Virginia"} } } NOTE

By preventing terms from being overridden, protection also prevents any adaptation of a term (e.g., defining a more precise datatype, restricting the term's use to lists, etc.). This kind of adaptation is frequent with some general purpose contexts, for which protection would therefore hinder their usability. As a consequence, context publishers should use this feature with care.

NOTE

Protected term definitions are a new feature in JSON-LD 1.1.

4.2 Describing Values

This section is non-normative.

Values are leaf nodes in a graph associated with scalar values such as strings, dates, times, and other such atomic values.

4.2.1 Typed Values

This section is non-normative.

A value with an associated type, also known as a typed value, is indicated by associating a value with an IRI which indicates the value's type. Typed values may be expressed in JSON-LD in three ways:

By utilizing the @type keyword when defining a term within an @context section. By utilizing a value object. By using a native JSON type such as number, true, or false.

The first example uses the @type keyword to associate a type with a particular term in the @context:

EXAMPLE 59: Expanded term definition with type coercion Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "modified": { "@id": "http://purl.org/dc/terms/modified", "@type": "http://www.w3.org/2001/XMLSchema#dateTime" } }, ... "@id": "http://example.com/docs/1", "modified": "2010-05-29T14:17:39+02:00", ... }

The modified key's value above is automatically interpreted as a dateTime value because of the information specified in the @context. The example tabs show how a JSON-LD processor will interpret the data.

The second example uses the expanded form of setting the type information in the body of a JSON-LD document:

EXAMPLE 60: Expanded value with type Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "modified": { "@id": "http://purl.org/dc/terms/modified" } }, ... "modified": { "@value": "2010-05-29T14:17:39+02:00", "@type": "http://www.w3.org/2001/XMLSchema#dateTime" } ... }

Both examples above would generate the value 2010-05-29T14:17:39+02:00 with the type http://www.w3.org/2001/XMLSchema#dateTime. Note that it is also possible to use a term or a compact IRI to express the value of a type.

NOTE

The @type keyword is also used to associate a type with a node. The concept of a node type and a value type are distinct. For more on adding types to nodes, see § 3.5 Specifying the Type.

NOTE

When expanding, an @type defined within a term definition can be associated with a string value to create an expanded value object, which is described in § 4.2.3 Type Coercion. Type coercion only takes place on string values, not for values which are maps, such as node objects and value objects in their expanded form.

A node type specifies the type of thing that is being described, like a person, place, event, or web page. A value type specifies the data type of a particular value, such as an integer, a floating point number, or a date.

EXAMPLE 61: Example demonstrating the context-sensitivity for @type { ... "@id": "http://example.org/posts#TripToWestVirginia", "@type": "http://schema.org/BlogPosting", ← This is a node type "http://purl.org/dc/terms/modified": { "@value": "2010-05-29T14:17:39+02:00", "@type": "http://www.w3.org/2001/XMLSchema#dateTime" ← This is a value type } ... }

The first use of @type associates a node type (http://schema.org/BlogPosting) with the node, which is expressed using the @id keyword. The second use of @type associates a value type (http://www.w3.org/2001/XMLSchema#dateTime) with the value expressed using the @value keyword. As a general rule, when @value and @type are used in the same map, the @type keyword is expressing a value type. Otherwise, the @type keyword is expressing a node type. The example above expresses the following data:

EXAMPLE 62: Example demonstrating the context-sensitivity for @type (statements) Compacted (Input) Turtle Open in playground Subject Property Value Value Type http://example.org/posts#TripToWestVirginia rdf:type schema:BlogPosting http://example.org/posts#TripToWestVirginia dcterms:modified 2010-05-29T14:17:39+02:00 xsd:dateTime 4.2.2 JSON Literals

This section is non-normative.

At times, it is useful to include JSON within JSON-LD that is not interpreted as JSON-LD. Generally, a JSON-LD processor will ignore properties which don't map to IRIs, but this causes them to be excluded when performing various algorithmic transformations. But, when the data that is being described is, itself, JSON, it's important that it survives algorithmic transformations.

Warning

JSON-LD is intended to allow native JSON to be interpreted through the use of a context. The use of JSON literals creates blobs of data which are not available for interpretation. It is for use only in the rare cases that JSON cannot be represented as JSON-LD.

When a term is defined with @type set to @json, a JSON-LD processor will treat the value as a JSON literal, rather than interpreting it further as JSON-LD. In the expanded document form, such JSON will become the value of @value within a value object having "@type": "@json".

When transformed into RDF, the JSON literal will have a lexical form based on a specific serialization of the JSON, as described in Compaction algorithm of [JSON-LD11-API] and the JSON datatype.

The following example shows an example of a JSON Literal contained as the value of a property. Note that the RDF results use a canonicalized form of the JSON to ensure interoperability between different processors. JSON canonicalization is described in Data Round Tripping in [JSON-LD11-API].

EXAMPLE 63: JSON Literal Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "e": {"@id": "http://example.com/vocab/json", "@type": "@json"} }, "e": [ 56.0, { "d": true, "10": null, "1": [ ] } ] } NOTE

Generally, when a JSON-LD processor encounters null, the associated entry or value is removed. However, null is a valid JSON token; when used as the value of a JSON literal, a null value will be preserved.

4.2.3 Type Coercion

This section is non-normative.

JSON-LD supports the coercion of string values to particular data types. Type coercion allows someone deploying JSON-LD to use string property values and have those values be interpreted as typed values by associating an IRI with the value in the expanded value object representation. Using type coercion, string value representation can be used without requiring the data type to be specified explicitly with each piece of data.

Type coercion is specified within an expanded term definition using the @type key. The value of this key expands to an IRI. Alternatively, the keyword @id or @vocab may be used as value to indicate that within the body of a JSON-LD document, a string value of a term coerced to @id or @vocab is to be interpreted as an IRI. The difference between @id and @vocab is how values are expanded to IRIs. @vocab first tries to expand the value by interpreting it as term. If no matching term is found in the active context, it tries to expand it as an IRI or a compact IRI if there's a colon in the value; otherwise, it will expand the value using the active context's vocabulary mapping, if present. Values coerced to @id in contrast are expanded as an IRI or a compact IRI if a colon is present; otherwise, they are interpreted as relative IRI references.

NOTE

The ability to coerce a value using a term definition is distinct from setting one or more types on a node object, as the former does not result in new data being added to the graph, while the latter manages node types through adding additional relationships to the graph.

Terms or compact IRIs used as the value of a @type key may be defined within the same context. This means that one may specify a term like xsd and then use xsd:integer within the same context definition.

The example below demonstrates how a JSON-LD author can coerce values to typed values and IRIs.

EXAMPLE 64: Expanded term definition with types Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "xsd": "http://www.w3.org/2001/XMLSchema#", "name": "http://xmlns.com/foaf/0.1/name", "age": { "@id": "http://xmlns.com/foaf/0.1/age", "@type": "xsd:integer" }, "homepage": { "@id": "http://xmlns.com/foaf/0.1/homepage", "@type": "@id" } }, "@id": "http://example.com/people#john", "name": "John Smith", "age": "41", "homepage": [ "http://personal.example.org/", "http://work.example.com/jsmith/" ] }

It is important to note that terms are only used in expansion for vocabulary-relative positions, such as for keys and values of map entries. Values of @id are considered to be document-relative, and do not use term definitions for expansion. For example, consider the following:

EXAMPLE 65: Term expansion for values, not identifiers Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@base": "http://example1.com/", "@vocab": "http://example2.com/", "knows": {"@type": "@vocab"} }, "@id": "fred", "knows": [ {"@id": "barney", "mnemonic": "the sidekick"}, "barney" ] }

The unexpected result is that "barney" expands to both http://example1.com/barney and http://example2.com/barney, depending where it is encountered. String values interpreted as IRIs because of the associated term definitions are typically considered to be document-relative. In some cases, it makes sense to interpret these relative to the vocabulary, prescribed using "@type": "@vocab" in the term definition, though this can lead to unexpected consequences such as these.

In the previous example, "barney" appears twice, once as the value of @id, which is always interpreted as a document-relative IRI, and once as the value of "fred", which is defined to be vocabulary-relative, thus the different expanded values.

For more on this see § 4.1.2 Default Vocabulary.

A variation on the previous example using "@type": "@id" instead of @vocab illustrates the behavior of interpreting "barney" relative to the document:

EXAMPLE 66: Terms not expanded when document-relative Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@base": "http://example1.com/", "@vocab": "http://example2.com/", "knows": {"@type": "@id"} }, "@id": "fred", "knows": [ {"@id": "barney", "mnemonic": "the sidekick"}, "barney" ] } NOTE

The triple ex1:fred ex2:knows ex1:barney . is emitted twice, but exists only once in an output dataset, as it is a duplicate triple.

Terms may also be defined using IRIs or compact IRIs. This allows coercion rules to be applied to keys which are not represented as a simple term. For example:

EXAMPLE 67: Term definitions using IRIs and compact IRIs Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "xsd": "http://www.w3.org/2001/XMLSchema#", "foaf": "http://xmlns.com/foaf/0.1/", "foaf:age": { "@id": "http://xmlns.com/foaf/0.1/age", "@type": "xsd:integer" }, "http://xmlns.com/foaf/0.1/homepage": { "@type": "@id" } }, "foaf:name": "John Smith", "foaf:age": "41", "http://xmlns.com/foaf/0.1/homepage": [ "http://personal.example.org/", "http://work.example.com/jsmith/" ] }

In this case the @id definition in the term definition is optional. If it does exist, the IRI or compact IRI representing the term will always be expanded to IRI defined by the @id key—regardless of whether a prefix is defined or not.

Type coercion is always performed using the unexpanded value of the key. In the example above, that means that type coercion is done looking for foaf:age in the active context and not for the corresponding, expanded IRI http://xmlns.com/foaf/0.1/age.

NOTE

Keys in the context are treated as terms for the purpose of expansion and value coercion. At times, this may result in multiple representations for the same expanded IRI. For example, one could specify that dog and cat both expanded to http://example.com/vocab#animal. Doing this could be useful for establishing different type coercion or language specification rules.

4.2.4 String Internationalization

This section is non-normative.

At times, it is important to annotate a string with its language. In JSON-LD this is possible in a variety of ways. First, it is possible to define a default language for a JSON-LD document by setting the @language key in the context:

EXAMPLE 68: Setting the default language of a JSON-LD document Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "name": "http://example.org/name", "occupation": "http://example.org/occupation", ... "@language": "ja" }, "name": "花澄", "occupation": "科学者" }

The example above would associate the ja language tag with the two strings 花澄 and 科学者 Languages tags are defined in [BCP47]. The default language applies to all string values that are not type coerced.

To clear the default language for a subtree, @language can be set to null in an intervening context, such as a scoped context as follows:

EXAMPLE 69: Clearing default language { "@context": { ... "@version": 1.1, "@vocab": "http://example.com/", "@language": "ja", "details": { "@context": { "@language": null } } }, "name": "花澄", "details": {"occupation": "Ninja"} }

Second, it is possible to associate a language with a specific term using an expanded term definition:

EXAMPLE 70: Expanded term definition with language { "@context": { ... "ex": "http://example.com/vocab/", "@language": "ja", "name": { "@id": "ex:name", "@language": null }, "occupation": { "@id": "ex:occupation" }, "occupation_en": { "@id": "ex:occupation", "@language": "en" }, "occupation_cs": { "@id": "ex:occupation", "@language": "cs" } }, "name": "Yagyū Muneyoshi", "occupation": "忍者", "occupation_en": "Ninja", "occupation_cs": "Nindža", ... }

The example above would associate 忍者 with the specified default language tag ja, Ninja with the language tag en, and Nindža with the language tag cs. The value of name, Yagyū Muneyoshi wouldn't be associated with any language tag since @language was reset to null in the expanded term definition.

NOTE

Language associations are only applied to plain strings. Typed values or values that are subject to type coercion are not language tagged.

Just as in the example above, systems often need to express the value of a property in multiple languages. Typically, such systems also try to ensure that developers have a programmatically easy way to navigate the data structures for the language-specific data. In this case, language maps may be utilized.

EXAMPLE 71: Language map expressing a property in three languages { "@context": { ... "occupation": { "@id": "ex:occupation", "@container": "@language" } }, "name": "Yagyū Muneyoshi", "occupation": { "ja": "忍者", "en": "Ninja", "cs": "Nindža" } ... }

The example above expresses exactly the same information as the previous example but consolidates all values in a single property. To access the value in a specific language in a programming language supporting dot-notation accessors for object properties, a developer may use the property.language pattern (when languages are limited to the primary language sub-tag, and do not depend on other sub-tags, such as "en-us"). For example, to access the occupation in English, a developer would use the following code snippet: obj.occupation.en.

Third, it is possible to override the default language by using a value object:

EXAMPLE 72: Overriding default language using an expanded value { "@context": { ... "@language": "ja" }, "name": "花澄", "occupation": { "@value": "Scientist", "@language": "en" } }

This makes it possible to specify a plain string by omitting the @language tag or setting it to null when expressing it using a value object:

EXAMPLE 73: Removing language information using an expanded value { "@context": { ... "@language": "ja" }, "name": { "@value": "Frank" }, "occupation": { "@value": "Ninja", "@language": "en" }, "speciality": "手裏剣" }

See § 9.8 Language Maps for a description of using language maps to set the language of mapped values.

4.2.4.1 Base Direction

This section is non-normative.

It is also possible to annotate a string, or language-tagged string, with its base direction. As with language, it is possible to define a default base direction for a JSON-LD document by setting the @direction key in the context:

EXAMPLE 74: Setting the default base direction of a JSON-LD document Compacted (Input) Expanded (Result) Statements Turtle (drops direction) Turtle (with datatype) Turtle (with bnode structure) Open in playground { "@context": { "title": "http://example.org/title", "publisher": "http://example.org/publisher", ... "@language": "ar-EG", "@direction": "rtl" }, "title": "HTML و CSS: تصميم و إنشاء مواقع الويب", "publisher": "مكتبة" }

The example above would associate the ar-EG language tag and "rtl" base direction with the two strings HTML و CSS: تصميم و إنشاء مواقع الويب and مكتبة. The default base direction applies to all string values that are not type coerced.

To clear the default base direction for a subtree, @direction can be set to null in an intervening context, such as a scoped context as follows:

EXAMPLE 75: Clearing default base direction { "@context": { ... "@version": 1.1, "@vocab": "http://example.com/", "@language": "ar-EG", "@direction": "rtl", "details": { "@context": { "@direction": null } } }, "title": "HTML و CSS: تصميم و إنشاء مواقع الويب", "details": {"genre": "Technical Publication"} }

Second, it is possible to associate a base direction with a specific term using an expanded term definition:

EXAMPLE 76: Expanded term definition with language and direction { "@context": { ... "@version": 1.1, "@language": "ar-EG", "@direction": "rtl", "ex": "http://example.com/vocab/", "publisher": { "@id": "ex:publisher", "@direction": null }, "title": { "@id": "ex:title" }, "title_en": { "@id": "ex:title", "@language": "en", "@direction": "ltr" } }, "publisher": "مكتبة", "title": "HTML و CSS: تصميم و إنشاء مواقع الويب", "title_en": "HTML and CSS: Design and Build Websites", ... }

The example above would create three properties:

Subject Property Value Language Direction _:b0 http://example.com/vocab/publisher مكتبة ar-EG _:b0 http://example.com/vocab/title HTML و CSS: تصميم و إنشاء مواقع الويب ar-EG rtl _:b0 http://example.com/vocab/title HTML and CSS: Design and Build Websites en ltr NOTE

Base direction associations are only applied to plain strings and language-tagged strings. Typed values or values that are subject to type coercion are not given a base direction.

Third, it is possible to override the default base direction by using a value object:

EXAMPLE 77: Overriding default language and default base direction using an expanded value { "@context": { ... "@language": "ar-EG", "@direction": "rtl" }, "title": "HTML و CSS: تصميم و إنشاء مواقع الويب", "author": { "@value": "Jon Duckett", "@language": "en", "@direction": null } }

See Strings on the Web: Language and Direction Metadata [string-meta] for a deeper discussion of base direction.

4.3 Value Ordering

This section is non-normative.

A JSON-LD author can express multiple values in a compact way by using arrays. Since graphs do not describe ordering for links between nodes, arrays in JSON-LD do not convey any ordering of the contained elements by default. This is exactly the opposite from regular JSON arrays, which are ordered by default. For example, consider the following simple document:

EXAMPLE 78: Multiple values with no inherent order Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": {"foaf": "http://xmlns.com/foaf/0.1/"}, ... "@id": "http://example.org/people#joebob", "foaf:nick": [ "joe", "bob", "JB" ], ... }

Multiple values may also be expressed using the expanded form:

EXAMPLE 79: Using an expanded form to set multiple values Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": {"dcterms": "http://purl.org/dc/terms/"}, "@id": "http://example.org/articles/8", "dcterms:title": [ { "@value": "Das Kapital", "@language": "de" }, { "@value": "Capital", "@language": "en" } ] } NOTE

The example shown above would generates statement, again with no inherent order.

Although multiple values of a property are typically of the same type, JSON-LD places no restriction on this, and a property may have values of different types:

EXAMPLE 80: Multiple array values of different types Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": {"ex": "http://example.org/"}, "@id": "http://example.org/people#michael", "ex:name": [ "Michael", {"@value": "Mike"}, {"@value": "Miguel", "@language": "es"}, { "@id": "https://www.wikidata.org/wiki/Q4927524" }, 42 ] } NOTE

When viewed as statements, the values have no inherent order.

4.3.1 Lists

This section is non-normative.

As the notion of ordered collections is rather important in data modeling, it is useful to have specific language support. In JSON-LD, a list may be represented using the @list keyword as follows:

EXAMPLE 81: An ordered collection of values in JSON-LD Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": {"foaf": "http://xmlns.com/foaf/0.1/"}, ... "@id": "http://example.org/people#joebob", "foaf:nick": { "@list": [ "joe", "bob", "jaybee" ] }, ... }

This describes the use of this array as being ordered, and order is maintained when processing a document. If every use of a given multi-valued property is a list, this may be abbreviated by setting @container to @list in the context:

EXAMPLE 82: Specifying that a collection is ordered in the context Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { ... "nick": { "@id": "http://xmlns.com/foaf/0.1/nick", "@container": "@list" } }, ... "@id": "http://example.org/people#joebob", "nick": [ "joe", "bob", "jaybee" ], ... }

The implementation of lists in RDF depends on linking anonymous nodes together using the properties rdf:first and rdf:rest, with the end of the list defined as the resource rdf:nil, as the "statements" tab illustrates. This allows order to be represented within an unordered set of statements.

Both JSON-LD and Turtle provide shortcuts for representing ordered lists.

In JSON-LD 1.1, lists of lists, where the value of a list object, may itself be a list object, are fully supported.

Note that the "@container": "@list" definition recursively describes array values of lists as being, themselves, lists. For example, in The GeoJSON Format (see [RFC7946]), coordinates are an ordered list of positions, which are represented as an array of two or more numbers:

EXAMPLE 83: Coordinates expressed in GeoJSON { "type": "Feature", "bbox": [-10.0, -10.0, 10.0, 10.0], "geometry": { "type": "Polygon", "coordinates": [ [ [-10.0, -10.0], [10.0, -10.0], [10.0, 10.0], [-10.0, -10.0] ] ] } //... }

For these examples, it's important that values expressed within bbox and coordinates maintain their order, which requires the use of embedded list structures. In JSON-LD 1.1, we can express this using recursive lists, by simply adding the appropriate context definition:

EXAMPLE 84: Coordinates expressed in JSON-LD Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@vocab": "https://purl.org/geojson/vocab#", "type": "@type", "bbox": {"@container": "@list"}, "coordinates": {"@container": "@list"} }, "type": "Feature", "bbox": [-10.0, -10.0, 10.0, 10.0], "geometry": { "type": "Polygon", "coordinates": [ [ [-10.0, -10.0], [10.0, -10.0], [10.0, 10.0], [-10.0, -10.0] ] ] } //... }

Note that coordinates includes three levels of lists.

Values of terms associated with an @list container are always represented in the form of an array, even if there is just a single value or no value at all.

4.3.2 Sets

This section is non-normative.

While @list is used to describe ordered lists, the @set keyword is used to describe unordered sets. The use of @set in the body of a JSON-LD document is optimized away when processing the document, as it is just syntactic sugar. However, @set is helpful when used within the context of a document. Values of terms associated with an @set container are always represented in the form of an array, even if there is just a single value that would otherwise be optimized to a non-array form in compact form (see § 5.2 Compacted Document Form). This makes post-processing of JSON-LD documents easier as the data is always in array form, even if the array only contains a single value.

EXAMPLE 85: An unordered collection of values in JSON-LD Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": {"foaf": "http://xmlns.com/foaf/0.1/"}, ... "@id": "http://example.org/people#joebob", "foaf:nick": { "@set": [ "joe", "bob", "jaybee" ] }, ... }

This describes the use of this array as being unordered, and order may change when processing a document. By default, arrays of values are unordered, but this may be made explicit by setting @container to @set in the context:

EXAMPLE 86: Specifying that a collection is unordered in the context Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { ... "nick": { "@id": "http://xmlns.com/foaf/0.1/nick", "@container": "@set" } }, ... "@id": "http://example.org/people#joebob", "nick": [ "joe", "bob", "jaybee" ], ... }

Since JSON-LD 1.1, the @set keyword may be combined with other container specifications within an expanded term definition to similarly cause compacted values of indexes to be consistently represented using arrays. See § 4.6 Indexed Values for a further discussion.

4.3.3 Using @set with @type

This section is non-normative.

Unless the processing mode is set to json-ld-1.0, @type may be used with an expanded term definition with @container set to @set; no other entries may be set within such an expanded term definition. This is used by the Compaction algorithm to ensure that the values of @type (or an alias) are always represented in an array.

EXAMPLE 87: Setting @container: @set on @type { "@context": { "@version": 1.1, "@type": {"@container": "@set"} }, "@type": ["http:/example.org/type"] } 4.4 Nested Properties

This section is non-normative.

Many JSON APIs separate properties from their entities using an intermediate object; in JSON-LD these are called nested properties. For example, a set of possible labels may be grouped under a common property:

EXAMPLE 88: Nested properties Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "skos": "http://www.w3.org/2004/02/skos/core#", "labels": "@nest", "main_label": {"@id": "skos:prefLabel"}, "other_label": {"@id": "skos:altLabel"}, "homepage": {"@id": "http://xmlns.com/foaf/0.1/homepage", "@type": "@id"} }, "@id": "http://example.org/myresource", "homepage": "http://example.org", "labels": { "main_label": "This is the main label for my resource", "other_label": "This is the other label" } }

By defining labels using the keyword @nest, a JSON-LD processor will ignore the nesting created by using the labels property and process the contents as if it were declared directly within containing object. In this case, the labels property is semantically meaningless. Defining it as equivalent to @nest causes it to be ignored when expanding, making it equivalent to the following:

EXAMPLE 89: Nested properties folded into containing object Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "skos": "http://www.w3.org/2004/02/skos/core#", "main_label": {"@id": "skos:prefLabel"}, "other_label": {"@id": "skos:altLabel"}, "homepage": {"@id": "http://xmlns.com/foaf/0.1/homepage", "@type": "@id"} }, "@id": "http://example.org/myresource", "homepage": "http://example.org", "main_label": "This is the main label for my resource", "other_label": "This is the other label" }

Similarly, term definitions may contain a @nest property referencing a term aliased to @nest which will cause such properties to be nested under that aliased term when compacting. In the example below, both main_label and other_label are defined with "@nest": "labels", which will cause them to be serialized under labels when compacting.

EXAMPLE 90: Defining property nesting - Expanded Input [{ "@id": "http://example.org/myresource", "http://xmlns.com/foaf/0.1/homepage": [ {"@id": "http://example.org"} ], "http://www.w3.org/2004/02/skos/core#prefLabel": [ {"@value": "This is the main label for my resource"} ], "http://www.w3.org/2004/02/skos/core#altLabel": [ {"@value": "This is the other label"} ] }] EXAMPLE 91: Defining property nesting - Context { "@context": { "@version": 1.1, "skos": "http://www.w3.org/2004/02/skos/core#", "labels": "@nest", "main_label": {"@id": "skos:prefLabel", "@nest": "labels"}, "other_label": {"@id": "skos:altLabel", "@nest": "labels"}, "homepage": {"@id": "http://xmlns.com/foaf/0.1/homepage", "@type": "@id"} } } EXAMPLE 92: Defining property nesting Compacted (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "skos": "http://www.w3.org/2004/02/skos/core#", "labels": "@nest", "main_label": {"@id": "skos:prefLabel", "@nest": "labels"}, "other_label": {"@id": "skos:altLabel", "@nest": "labels"}, "homepage": {"@id": "http://xmlns.com/foaf/0.1/homepage", "@type": "@id"} }, "@id": "http://example.org/myresource", "homepage": "http://example.org", "labels": { "main_label": "This is the main label for my resource", "other_label": "This is the other label" } } NOTE

Nested properties are a new feature in JSON-LD 1.1.

4.5 Embedding

This section is non-normative.

Embedding is a JSON-LD feature that allows an author to use node objects as property values. This is a commonly used mechanism for creating a parent-child relationship between two nodes.

Without embedding, node objects can be linked by referencing the identifier of another node object. For example:

EXAMPLE 93: Referencing node objects Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@vocab": "http://xmlns.com/foaf/0.1/", "knows": {"@type": "@id"} }, "@graph": [{ "name": "Manu Sporny", "@type": "Person", "knows": "https://greggkellogg.net/foaf#me" }, { "@id": "https://greggkellogg.net/foaf#me", "@type": "Person", "name": "Gregg Kellogg" }] }

The previous example describes two node objects, for Manu and Gregg, with the knows property defined to treat string values as identifiers. Embedding allows the node object for Gregg to be embedded as a value of the knows property:

EXAMPLE 94: Embedding a node object as property value of another node object Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@vocab": "http://xmlns.com/foaf/0.1/" }, "@type": "Person", "name": "Manu Sporny", "knows": { "@id": "https://greggkellogg.net/foaf#me", "@type": "Person", "name": "Gregg Kellogg" } }

A node object, like the one used above, may be used in any value position in the body of a JSON-LD document.

While it is considered a best practice to identify nodes in a graph, at times this is impractical. In the data model, nodes without an explicit identifier are called blank nodes, which can be represented in a serialization such as JSON-LD using a blank node identifier. In the previous example, the top-level node for Manu does not have an identifier, and does not need one to describe it within the data model. However, if we were to want to describe a knows relationship from Gregg to Manu, we would need to introduce a blank node identifier (here _:b0).

EXAMPLE 95: Referencing an unidentified node Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@vocab": "http://xmlns.com/foaf/0.1/" }, "@id": ":b0", "@type": "Person", "name": "Manu Sporny", "knows": { "@id": "https://greggkellogg.net/foaf#me", "@type": "Person", "name": "Gregg Kellogg", "knows": {"@id": ":b0"} } }

Blank node identifiers may be automatically introduced by algorithms such as flattening, but they are also useful for authors to describe such relationships directly.

4.5.1 Identifying Blank Nodes

This section is non-normative.

At times, it becomes necessary to be able to express information without being able to uniquely identify the node with an IRI. This type of node is called a blank node. JSON-LD does not require all nodes to be identified using @id. However, some graph topologies may require identifiers to be serializable. Graphs containing loops, e.g., cannot be serialized using embedding alone, @id must be used to connect the nodes. In these situations, one can use blank node identifiers, which look like IRIs using an underscore (_) as scheme. This allows one to reference the node locally within the document, but makes it impossible to reference the node from an external document. The blank node identifier is scoped to the document in which it is used.

EXAMPLE 96: Specifying a local blank node identifier Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": "http://schema.org/", ... "@id": ":n1", "name": "Secret Agent 1", "knows": { "name": "Secret Agent 2", "knows": { "@id": ":n1" } } }

The example above contains information about two secret agents that cannot be identified with an IRI. While expressing that agent 1 knows agent 2 is possible without using blank node identifiers, it is necessary to assign agent 1 an identifier so that it can be referenced from agent 2.

It is worth noting that blank node identifiers may be relabeled during processing. If a developer finds that they refer to the blank node more than once, they should consider naming the node using a dereferenceable IRI so that it can also be referenced from other documents.

4.6 Indexed Values

This section is non-normative.

Sometimes multiple property values need to be accessed in a more direct fashion than iterating though multiple array values. JSON-LD provides an indexing mechanism to allow the use of an intermediate map to associate specific indexes with associated values.

Data Indexing As described in § 4.6.1 Data Indexing, data indexing allows an arbitrary key to reference a node or value. Language Indexing As described in § 4.6.2 Language Indexing, language indexing allows a language to reference a string and be interpreted as the language associated with that string. Node Identifier Indexing As described in § 4.6.3 Node Identifier Indexing, node identifier indexing allows an IRI to reference a node and be interpreted as the identifier of that node. Node Type Indexing As described in § 4.6.4 Node Type Indexing, node type indexing allows an IRI to reference a node and be interpreted as a type of that node.

See § 4.9 Named Graphs for other uses of indexing in JSON-LD.

4.6.1 Data Indexing

This section is non-normative.

Databases are typically used to make access to data more efficient. Developers often extend this sort of functionality into their application data to deliver similar performance gains. This data may have no meaning from a Linked Data standpoint, but is still useful for an application.

JSON-LD introduces the notion of index maps that can be used to structure data into a form that is more efficient to access. The data indexing feature allows an author to structure data using a simple key-value map where the keys do not map to IRIs. This enables direct access to data instead of having to scan an array in search of a specific item. In JSON-LD such data can be specified by associating the @index keyword with a @container declaration in the context:

EXAMPLE 97: Indexing data in JSON-LD Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "schema": "http://schema.org/", "name": "schema:name", "body": "schema:articleBody", "athletes": { "@id": "schema:athlete", "@container": "@index" }, "position": "schema:jobTitle" }, "@id": "http://example.com/", "@type": "schema:SportsTeam", "name": "San Francisco Giants", "athletes": { "catcher": { "@type": "schema:Person", "name": "Buster Posey", "position": "Catcher" }, "pitcher": { "@type": "schema:Person", "name": "Madison Bumgarner", "position": "Starting Pitcher" }, .... } }

In the example above, the athletes term has been marked as an index map. The catcher and pitcher keys will be ignored semantically, but preserved syntactically, by the JSON-LD Processor. If used in JavaScript, this can allow a developer to access a particular athlete using the following code snippet: obj.athletes.pitcher.

The interpretation of the data is expressed in the statements table. Note how the index keys do not appear in the statements, but would continue to exist if the document were compacted or expanded (see § 5.2 Compacted Document Form and § 5.1 Expanded Document Form) using a JSON-LD processor.

Warning

As data indexes are not preserved when round-tripping to RDF; this feature should be used judiciously. Often, other indexing mechanisms, which are preserved, are more appropriate.

The value of @container can also be an array containing both @index and @set. When compacting, this ensures that a JSON-LD Processor will use the array form for all values of indexes.

Unless the processing mode is set to json-ld-1.0, the special index @none is used for indexing data which does not have an associated index, which is useful to maintain a normalized representation.

EXAMPLE 98: Indexing data using @none Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "schema": "http://schema.org/", "name": "schema:name", "body": "schema:articleBody", "athletes": { "@id": "schema:athlete", "@container": "@index" }, "position": "schema:jobTitle" }, "@id": "http://example.com/", "@type": "schema:SportsTeam", "name": "San Francisco Giants", "athletes": { "catcher": { "@type": "schema:Person", "name": "Buster Posey", "position": "Catcher" }, "pitcher": { "@type": "schema:Person", "name": "Madison Bumgarner", "position": "Starting Pitcher" }, "@none": { "name": "Lou Seal", "position": "Mascot" }, .... } } 4.6.1.1 Property-based data indexing

This section is non-normative.

In its simplest form (as in the examples above), data indexing assigns no semantics to the keys of an index map. However, in some situations, the keys used to index objects are semantically linked to these objects, and should be preserved not only syntactically, but also semantically.

Unless the processing mode is set to json-ld-1.0, "@container": "@index" in a term description can be accompanied with an "@index" key. The value of that key must map to an IRI, which identifies the semantic property linking each object to its key.

EXAMPLE 99: Property-based data indexing Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "schema": "http://schema.org/", "name": "schema:name", "body": "schema:articleBody", "athletes": { "@id": "schema:athlete", "@container": "@index", "@index": "schema:jobTitle" } }, "@id": "http://example.com/", "@type": "schema:SportsTeam", "name": "San Francisco Giants", "athletes": { "Catcher": { ↑ "Catcher" will add "schema:jobTitle": "Catcher" when expanded "@type": "schema:Person", "name": "Buster Posey" }, "Starting Pitcher": { "@type": "schema:Person", "name": "Madison Bumgarner" }, .... } } NOTE

When using property-based data indexing, index maps can only be used on node objects, not value objects or graph objects. Value objects are restricted to have only certain keys and do not support arbitrary properties.

4.6.2 Language Indexing

This section is non-normative.

JSON which includes string values in multiple languages may be represented using a language map to allow for easily indexing property values by language tag. This enables direct access to language values instead of having to scan an array in search of a specific item. In JSON-LD such data can be specified by associating the @language keyword with a @container declaration in the context:

EXAMPLE 100: Indexing languaged-tagged strings in JSON-LD Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "vocab": "http://example.com/vocab/", "label": { "@id": "vocab:label", "@container": "@language" } }, "@id": "http://example.com/queen", "label": { "en": "The Queen", "de": [ "Die Königin", "Ihre Majestät" ] } }

In the example above, the label term has been marked as a language map. The en and de keys are implicitly associated with their respective values by the JSON-LD Processor. This allows a developer to access the German version of the label using the following code snippet: obj.label.de, which, again, is only appropriate when languages are limited to the primary language sub-tag and do not depend on other sub-tags, such as "de-at".

The value of @container can also be an array containing both @language and @set. When compacting, this ensures that a JSON-LD Processor will use the array form for all values of language tags.

EXAMPLE 101: Indexing languaged-tagged strings in JSON-LD with @set representation Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "vocab": "http://example.com/vocab/", "label": { "@id": "vocab:label", "@container": ["@language", "@set"] } }, "@id": "http://example.com/queen", "label": { "en": ["The Queen"], "de": [ "Die Königin", "Ihre Majestät" ] } }

Unless the processing mode is set to json-ld-1.0, the special index @none is used for indexing strings which do not have a language; this is useful to maintain a normalized representation for string values not having a datatype.

EXAMPLE 102: Indexing languaged-tagged strings using @none for no language Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "vocab": "http://example.com/vocab/", "label": { "@id": "vocab:label", "@container": "@language" } }, "@id": "http://example.com/queen", "label": { "en": "The Queen", "de": [ "Die Königin", "Ihre Majestät" ], "@none": "The Queen" } } 4.6.3 Node Identifier Indexing

This section is non-normative.

In addition to index maps, JSON-LD introduces the notion of id maps for structuring data. The id indexing feature allows an author to structure data using a simple key-value map where the keys map to IRIs. This enables direct access to associated node objects instead of having to scan an array in search of a specific item. In JSON-LD such data can be specified by associating the @id keyword with a @container declaration in the context:

EXAMPLE 103: Indexing data in JSON-LD by node identifiers Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "schema": "http://schema.org/", "name": "schema:name", "body": "schema:articleBody", "words": "schema:wordCount", "post": { "@id": "schema:blogPost", "@container": "@id", "@context": { "@base": "http://example.com/posts/" } } }, "@id": "http://example.com/", "@type": "schema:Blog", "name": "World Financial News", "post": { "1/en": { "body": "World commodities were up today with heavy trading of crude oil...", "words": 1539 }, "1/de": { "body": "Die Werte an Warenbörsen stiegen im Sog eines starken Handels von Rohöl...", "words": 1204 } } }

In the example above, the post term has been marked as an id map. The http://example.com/posts/1/en and http://example.com/posts/1/de keys will be interpreted as the @id property of the node object value.

The interpretation of the data above is exactly the same as that in § 4.6.1 Data Indexing using a JSON-LD processor.

The value of @container can also be an array containing both @id and @set. When compacting, this ensures that a JSON-LD processor will use the array form for all values of node identifiers.

EXAMPLE 104: Indexing data in JSON-LD by node identifiers with @set representation Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "schema": "http://schema.org/", "name": "schema:name", "body": "schema:articleBody", "words": "schema:wordCount", "post": { "@id": "schema:blogPost", "@container": ["@id", "@set"] } }, "@id": "http://example.com/", "@type": "schema:Blog", "name": "World Financial News", "post": { "http://example.com/posts/1/en": [{ "body": "World commodities were up today with heavy trading of crude oil...", "words": 1539 }], "http://example.com/posts/1/de": [{ "body": "Die Werte an Warenbörsen stiegen im Sog eines starken Handels von Rohöl...", "words": 1204 }] } }

The special index @none is used for indexing node objects which do not have an @id, which is useful to maintain a normalized representation. The @none index may also be a term which expands to @none, such as the term none used in the example below.

EXAMPLE 105: Indexing data in JSON-LD by node identifiers using @none Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "schema": "http://schema.org/", "name": "schema:name", "body": "schema:articleBody", "words": "schema:wordCount", "post": { "@id": "schema:blogPost", "@container": "@id" }, "none": "@none" }, "@id": "http://example.com/", "@type": "schema:Blog", "name": "World Financial News", "post": { "http://example.com/posts/1/en": { "body": "World commodities were up today with heavy trading of crude oil...", "words": 1539 }, "http://example.com/posts/1/de": { "body": "Die Werte an Warenbörsen stiegen im Sog eines starken Handels von Rohöl...", "words": 1204 }, "none": { "body": "Description for object without an @id", "words": 20 } } } NOTE

Id maps are a new feature in JSON-LD 1.1.

4.6.4 Node Type Indexing

This section is non-normative.

In addition to id and index maps, JSON-LD introduces the notion of type maps for structuring data. The type indexing feature allows an author to structure data using a simple key-value map where the keys map to IRIs. This enables data to be structured based on the @type of specific node objects. In JSON-LD such data can be specified by associating the @type keyword with a @container declaration in the context:

EXAMPLE 106: Indexing data in JSON-LD by type Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "schema": "http://schema.org/", "name": "schema:name", "affiliation": { "@id": "schema:affiliation", "@container": "@type" } }, "name": "Manu Sporny", "affiliation": { "schema:Corporation": { "@id": "https://digitalbazaar.com/", "name": "Digital Bazaar" }, "schema:ProfessionalService": { "@id": "https://spec-ops.io", "name": "Spec-Ops" } } }

In the example above, the affiliation term has been marked as a type map. The schema:Corporation and schema:ProfessionalService keys will be interpreted as the @type property of the node object value.

The value of @container can also be an array containing both @type and @set. When compacting, this ensures that a JSON-LD processor will use the array form for all values of types.

EXAMPLE 107: Indexing data in JSON-LD by type with @set representation Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "schema": "http://schema.org/", "name": "schema:name", "affiliation": { "@id": "schema:affiliation", "@container": ["@type", "@set"] } }, "name": "Manu Sporny", "affiliation": { "schema:Corporation": [{ "@id": "https://digitalbazaar.com/", "name": "Digital Bazaar" }], "schema:ProfessionalService": [{ "@id": "https://spec-ops.io", "name": "Spec-Ops" }] } }

The special index @none is used for indexing node objects which do not have an @type, which is useful to maintain a normalized representation. The @none index may also be a term which expands to @none, such as the term none used in the example below.

EXAMPLE 108: Indexing data in JSON-LD by type using @none Compacted (Input) Expanded (Result) Statements Turtle Open in playground { "@context": { "@version": 1.1, "schema": "http://schema.org/", "name": "schema:name", "affiliation": { "@id": "schema:affiliation", "@container": "@type" }, "none": "@none" }, "name": "Manu Sporny", "affiliation": { "schema:Corporation": { "@id": "https://digitalbazaar.com/", "name": "Digital Bazaar" }, "schema:ProfessionalService": { "@id": "https://spec-ops.io", "name": "Spec-Ops" }, "none": { "@id": "https://greggkellogg.net/", "name": "Gregg Kellogg" } } }

As with id maps, when used with @type, a container may also include @set to ensure that key values are always contained in an array.

NOTE

Type maps are a new feature in JSON-LD 1.1.

4.7 Included Nodes

This section is non-normative.

Sometimes it is also useful to list node objects as part of another node object. For instance, to represent a set of resources which are used by some other resource. Included blocks may be also be used to collect such secondary node objects which can be referenced from a primary node object. For an example, consider a node object containing a list of different items, some of which share some common elements:

EXAMPLE 109: Included Blocks { "@context": { "@version": 1.1, "@vocab": "http://example.org/", "classification": {"@type": "@vocab"} }, "@id": "http://example.org/org-1", "members": [{ "@id":"http://example.org/person-1", "name": "Manu Sporny", "classification": "employee" }, { "@id":"http://example.org/person-2", "name": "Dave Longley", "classification": "employee" }, { "@id": "http://example.org/person-3", "name": "Gregg Kellogg", "classification": "contractor" }], "@included": [{ "@id": "http://example.org/employee", "label": "An Employee" }, { "@id": "http://example.org/contractor", "label": "A Contractor" }] }

When flattened, this will move the employee and contractor elements from the included block into the outer array.

EXAMPLE 110: Flattened form for included blocks Flattened (Result) Statements Turtle Open in playground [{ "@id": "http://example.org/org-1", "http://example.org/members": [ {"@id": "http://example.org/person-1"}, {"@id": "http://example.org/person-2"}, {"@id": "http://example.org/person-3"} ] }, { "@id": "http://example.org/employee", "http://example.org/label": [{"@value": "An Employee"}] }, { "@id": "http://example.org/contractor", "http://example.org/label": [{"@value": "A Contractor"}] }, { "@id": "http://example.org/person-1", "http://example.org/name": [{"@value": "Manu Sporny"}], "http://example.org/classification": [ {"@id": "http://example.org/employee"} ] }, { "@id": "http://example.org/person-2", "http://example.org/name": [{"@value": "Dave Longley"}], "http://example.org/classification": [ {"@id": "http://example.org/employee"} ] }, { "@id": "http://example.org/person-3", "http://example.org/name": [{"@value": "Gregg Kellogg"}], "http://example.org/classification": [ {"@id": "http://example.org/contractor"} ] } ]

Included resources are described in Inclusion of Related Resources of JSON API [JSON.API] as a way to include related resources associated with some primary resource; @included provides an analogous possibility in JSON-LD.

As a by product of the use of @included within node objects, a map may contain only @included, to provide a feature similar to that described in § 4.1 Advanced Context Usage, where @graph is used to described disconnected nodes.

EXAMPLE 111: Describing disconnected nodes with @included Compacted (Input) Expanded (Result) Flattened Statements Turtle Open in playground { "@context": { "Person": "http://xmlns.com/foaf/0.1/Person", "name": "http://xmlns.com/foaf/0.1/name", "knows": {"@id": "http://xmlns.com/foaf/0.1/knows", "@type": "@id"} }, "@included": [{ "@id": "http://manu.sporny.org/about#manu", "@type": "Person", "name": "Manu Sporny", "knows": "https://greggkellogg.net/foaf#me" }, { "@id": "https://greggkellogg.net/foaf#me", "@type": "Person", "name": "Gregg Kellogg", "knows": "http://manu.sporny.org/about#manu" }] }

However, in contrast to @graph, @included does not interact with other properties contained within the same map, a feature discussed further in § 4.9 Named Graphs.

4.8 Reverse Properties

This section is non-normative.

JSON-LD serializes directed graphs. That means that every property points from a node to another node or value. However, in some cases, it is desirable to serialize in the reverse direction. Consider for example the case where a person and its children should be described in a document. If the used vocabulary does not provide a children property but just a parent property, every node representing a child would have to be expressed with a property pointing to the parent as in the following example.

EXAMPLE 112: A document with children linking to their parent Compacted (Input) Expanded (Result) Statements Turtle Open in playground [ { "@id": "#homer", "http://example.com/vocab#name": "Homer" }, { "@id": "#bart", "http://example.com/vocab#name": "Bart", "http://example.com/vocab#parent": { "@id": "#homer" } }, { "@id": "#lisa", "http://example.com/vocab#name": "Lisa", "http://example.com/vocab#parent": { "@id": "#homer" } } ]

Expressing such data is much simpler by using JSON-LD's @reverse keyword:

EXAMPLE 113: A person and its children using a reverse property Compacted (Input) Expanded (Result) Flattened Statements Turtle Open in playground { "@id": "#homer", "http://example.com/vocab#name": "Homer", "@reverse": { "http://example.com/vocab#parent": [ { "@id": "#bart", "http://example.com/vocab#name": "Bart" }, { "@id": "#lisa", "http://example.com/vocab#name": "Lisa" } ] } }

The @reverse keyword can also be used in expanded term definitions to create reverse properties as shown in the following example:

EXAMPLE 114: Using @reverse to define reverse properties Compacted (Input) Expanded (Result) Flattened Statements Turtle Open in playground { "@context": { "name": "http://example.com/vocab#name", "children": { "@reverse": "http://example.com/vocab#parent" } }, "@id": "#homer", "name": "Homer", "children": [ { "@id": "#bart", "name": "Bart" }, { "@id": "#lisa", "name": "Lisa" } ] } 4.9 Named Graphs

This section is non-normative.

At times, it is necessary to make statements about a graph itself, rather than just a single node. This can be done by grouping a set of nodes using the @graph keyword. A developer may also name data expressed using the @graph keyword by pairing it with an @id keyword as shown in the following example:

EXAMPLE 115: Identifying and making statements about a graph Compacted (Input) Expanded (Result) Statements TriG Open in playground { "@context": { "generatedAt": { "@id": "http://www.w3.org/ns/prov#generatedAtTime", "@type": "http://www.w3.org/2001/XMLSchema#dateTime" }, "Person": "http://xmlns.com/foaf/0.1/Person", "name": "http://xmlns.com/foaf/0.1/name", "knows": {"@id": "http://xmlns.com/foaf/0.1/knows", "@type": "@id"} }, "@id": "http://example.org/foaf-graph", "generatedAt": "2012-04-09T00:00:00", "@graph": [ { "@id": "http://manu.sporny.org/about#manu", "@type": "Person", "name": "Manu Sporny", "knows": "https://greggkellogg.net/foaf#me" }, { "@id": "https://greggkellogg.net/foaf#me", "@type": "Person", "name": "Gregg Kellogg", "knows": "http://manu.sporny.org/about#manu" } ] }

The example above expresses a named graph that is identified by the IRI http://example.org/foaf-graph. That graph is composed of the statements about Manu and Gregg. Metadata about the graph itself is expressed via the generatedAt property, which specifies when the graph was generated.

When a JSON-LD document's top-level structure is a map that contains no other keys than @graph and optionally @context (properties that are not mapped to an IRI or a keyword are ignored), @graph is considered to express the otherwise implicit default graph. This mechanism can be useful when a number of nodes exist at the document's top level that share the same context, which is, e.g., the case when a document is flattened. The @graph keyword collects such nodes in an array and allows the use of a shared context.

EXAMPLE 116: Using @graph to explicitly express the default graph Compacted (Input) Expanded (Result) Statements TriG Open in playground { "@context": { "@vocab": "http://xmlns.com/foaf/0.1/" }, "@graph": [ { "@id": "http://manu.sporny.org/about#manu", "@type": "Person", "name": "Manu Sporny" }, { "@id": "https://greggkellogg.net/foaf#me", "@type": "Person", "name": "Gregg Kellogg" } ] }

In this case, embedding can not be used as the graph contains unrelated nodes. This is equivalent to using multiple node objects in array and defining the @context within each node object:

EXAMPLE 117: Context needs to be duplicated if @graph is not used Compacted (Input) Expanded (Result) Statements TriG Open in playground [ { "@context": { "@vocab": "http://xmlns.com/foaf/0.1/", "knows": {"@type": "@id"} }, "@id": "http://manu.sporny.org/about#manu", "@type": "Person", "name": "Manu Sporny", "knows": "https://greggkellogg.net/foaf#me" }, { "@context": { "@vocab": "http://xmlns.com/foaf/0.1/", "knows": {"@type": "@id"} }, "@id": "https://greggkellogg.net/foaf#me", "@type": "Person", "name": "Gregg Kellogg", "knows": "http://manu.sporny.org/about#manu" } ] 4.9.1 Graph Containers

This section is non-normative.

In some cases, it is useful to logically partition data into separate graphs, without making this explicit within the JSON expression. For example, a JSON document may contain data against which other metadata is asserted and it is useful to separate this data in the data model using the notion of named graphs, without the syntactic overhead associated with the @graph keyword.

An expanded term definition can use @graph as the value of @container. This indicates that values of this term should be considered to be named graphs, where the graph name is an automatically assigned blank node identifier creating an implicitly named graph. When expanded, these become simple graph objects.

A different example uses an anonymously named graph as follows:

EXAMPLE 118: Implicitly named graph Compacted (Input) Expanded (Result) Statements TriG Open in playground { "@context": { "@version": 1.1, "@base": "http://dbpedia.org/resource/", "said": "http://example.com/said", "wrote": {"@id": "http://example.com/wrote", "@container": "@graph"} }, "@id": "William_Shakespeare", "wrote": { "@id": "Richard_III_of_England", "said": "My kingdom for a horse" } }

The example above expresses an anonymously named graph making a statement. The default graph includes a statement saying that the subject wrote that statement. This is an example of separating statements into a named graph, and then making assertions about the statements contained within that named graph.

NOTE

Strictly speaking, the value of such a term is not a named graph, rather it is the graph name associated with the named graph, which exists separately within the dataset.

NOTE

Graph Containers are a new feature in JSON-LD 1.1.

4.9.2 Named Graph Data Indexing

This section is non-normative.

In addition to indexing node objects by index, graph objects may also be indexed by an index. By using the @graph container type, introduced in § 4.9.1 Graph Containers in addition to @index, an object value of such a property is treated as a key-value map where the keys do not map to IRIs, but are taken from an @index property associated with named graphs which are their values. When expanded, these must be simple graph objects

The following example describes a default graph referencing multiple named graphs using an index map.

EXAMPLE 119: Indexing graph data in JSON-LD Compacted (Input) Expanded (Result) Statements TriG Open in playground { "@context": { "@version": 1.1, "schema": "http://schema.org/", "name": "schema:name", "body": "schema:articleBody", "words": "schema:wordCount", "post": { "@id": "schema:blogPost", "@container": ["@graph", "@index"] } }, "@id": "http://example.com/", "@type": "schema:Blog", "name": "World Financial News", "post": { "en": { "@id": "http://example.com/posts/1/en", "body": "World commodities were up today with heavy trading of crude oil...", "words": 1539 }, "de": { "@id": "http://example.com/posts/1/de", "body": "Die Werte an Warenbörsen stiegen im Sog eines starken Handels von Rohöl...", "words": 1204 } } }

As with index maps, when used with @graph, a container may also include @set to ensure that key values are always contained in an array.

The special index @none is used for indexing graphs which do not have an @index key, which is useful to maintain a normalized representation. Note, however, that compacting a document where multiple unidentified named graphs are compacted using the @none index will result in the content of those graphs being merged. To prevent this, give each graph a distinct @index key.

EXAMPLE 120: Indexing graphs using @none for no index Compacted (Input) Expanded (Result) Statements TriG Open in playground { "@context": { "@version": 1.1, "schema": "http://schema.org/", "name": "schema:name", "body": "schema:articleBody", "words": "schema:wordCount", "post": { "@id": "schema:blogPost", "@container": ["@graph", "@index"] } }, "@id": "http://example.com/", "@type": "schema:Blog", "name": "World Financial News", "post": { "en": { "@id": "http://example.com/posts/1/en", "body": "World commodities were up today with heavy trading of crude oil...", "words": 1539 }, "@none": { "@id": "http://example.com/posts/1/no-language", "body": "Die Werte an Warenbörsen stiegen im Sog eines starken Handels von Rohöl...", "words": 1204 } } } NOTE

Named Graph Data Indexing is a new feature in JSON-LD 1.1.

4.9.3 Named Graph Indexing

This section is non-normative.

In addition to indexing node objects by identifier, graph objects may also be indexed by their graph name. By using the @graph container type, introduced in § 4.9.1 Graph Containers in addition to @id, an object value of such a property is treated as a key-value map where the keys represent the identifiers of named graphs which are their values.

The following example describes a default graph referencing multiple named graphs using an id map.

EXAMPLE 121: Referencing named graphs using an id map Compacted (Input) Expanded (Result) Statements TriG Open in playground { "@context": { "@version": 1.1, "generatedAt": { "@id": "http://www.w3.org/ns/prov#generatedAtTime", "@type": "http://www.w3.org/2001/XMLSchema#dateTime" }, "Person": "http://xmlns.com/foaf/0.1/Person", "name": "http://xmlns.com/foaf/0.1/name", "knows": { "@id": "http://xmlns.com/foaf/0.1/knows", "@type": "@id" }, "graphMap": { "@id": "http://example.org/graphMap", "@container": ["@graph", "@id"] } }, "@id": "http://example.org/foaf-graph", "generatedAt": "2012-04-09T00:00:00", "graphMap": { "http://manu.sporny.org/about": { "@id": "http://manu.sporny.org/about#manu", "@type": "Person", "name": "Manu Sporny", "knows": "https://greggkellogg.net/foaf#me" }, "https://greggkellogg.net/foaf": { "@id": "https://greggkellogg.net/foaf#me", "@type": "Person", "name": "Gregg Kellogg", "knows": "http://manu.sporny.org/about#manu" } } }

As with id maps, when used with @graph, a container may also include @set to ensure that key values are always contained in an array.

As with id maps, the special index @none is used for indexing named graphs which do not have an @id, which is useful to maintain a normalized representation. The @none index may also be a term which expands to @none. Note, however, that if multiple graphs are represented without an @id, they will be merged on expansion. To prevent this, use @none judiciously, and consider giving graphs their own distinct identifier.

EXAMPLE 122: Referencing named graphs using an id map with @none Compacted (Input) Expanded (Result) Statements TriG Open in playground { "@context": { "@version": 1.1, "generatedAt": { "@id": "http://www.w3.org/ns/prov#generatedAtTime", "@type": "http://www.w3.org/2001/XMLSchema#dateTime" }, "Person": "http://xmlns.com/foaf/0.1/Person", "name": "http://xmlns.com/foaf/0.1/name", "knows": {"@id": "http://xmlns.com/foaf/0.1/knows", "@type": "@id"}, "graphMap": { "@id": "http://example.org/graphMap", "@container": ["@graph", "@id"] } }, "@id": "http://example.org/foaf-graph", "generatedAt": "2012-04-09T00:00:00", "graphMap": { "@none": [{ "@id": "http://manu.sporny.org/about#manu", "@type": "Person", "name": "Manu Sporny", "knows": "https://greggkellogg.net/foaf#me" }, { "@id": "https://greggkellogg.net/foaf#me", "@type": "Person", "name": "Gregg Kellogg", "knows": "http://manu.sporny.org/about#manu" }] } } NOTE

Graph Containers are a new feature in JSON-LD 1.1.

4.10 Loading Documents

This section is non-normative.

The JSON-LD 1.1 Processing Algorithms and API specification [JSON-LD11-API] defines the interface to a JSON-LD Processor and includes a number of methods used for manipulating different forms of JSON-LD (see § 5. Forms of JSON-LD). This includes a general mechanism for loading remote documents, including referenced JSON-LD documents and remote contexts, and potentially extracting embedded JSON-LD from other formats such as [HTML]. This is more fully described in Remote Document and Context Retrieval in [JSON-LD11-API].

A documentLoader can be useful in a number of contexts where loading remote documents can be problematic:

Remote context documents should be cached to prevent overloading the location of the remote context for each request. Normally, an HTTP caching infrastructure might be expected to handle this, but in some contexts this might not be feasible. A documentLoader implementation might provide separate logic for performing such caching. Non-standard URL schemes may not be widely implemented, or may have behavior specific to a given application domain. A documentLoader can be defined to implement document retrieval semantics. Certain well-known contexts may be statically cached within a documentLoader implementation. This might be particularly useful in embedded applications, where it is not feasible, or even possible, to access remote documents. For security purposes, the act of remotely retrieving a document may provide a signal of application behavior. The judicious use of a documentLoader can isolate the application and reduce its online fingerprint. 5. Forms of JSON-LD

This section is non-normative.

As with many data formats, there is no single correct way to describe data in JSON-LD. However, as JSON-LD is used for describing graphs, certain transformations can be used to change the shape of the data, without changing its meaning as Linked Data.

Expanded Document Form Expansion is the process of taking a JSON-LD document and applying a context so that the @context is no longer necessary. This process is described further in § 5.1 Expanded Document Form. Compacted Document Form Compaction is the process of applying a provided context to an existing JSON-LD document. This process is described further in § 5.2 Compacted Document Form. Flattened Document Form Flattening is the process of extracting embedded nodes to the top level of the JSON tree, and replacing the embedded node with a reference, creating blank node identifiers as necessary. This process is described further in § 5.3 Flattened Document Form. Framed Document Form Framing is used to shape the data in a JSON-LD document, using an example frame document which is used to both match the flattened data and show an example of how the resulting data should be shaped. This process is described further in § 5.4 Framed Document Form. 5.1 Expanded Document Form

This section is non-normative.

The JSON-LD 1.1 Processing Algorithms and API specification [JSON-LD11-API] defines a method for expanding a JSON-LD document. Expansion is the process of taking a JSON-LD document and applying a context such that all IRIs, types, and values are expanded so that the @context is no longer necessary.

For example, assume the following JSON-LD input document:

EXAMPLE 123: Sample JSON-LD document to be expanded { "@context": { "name": "http://xmlns.com/foaf/0.1/name", "homepage": { "@id": "http://xmlns.com/foaf/0.1/homepage", "@type": "@id" } }, "name": "Manu Sporny", "homepage": "http://manu.sporny.org/" }

Running the JSON-LD Expansion algorithm against the JSON-LD input document provided above would result in the following output:

EXAMPLE 124: Expanded form for the previous example Expanded (Result) Statements Turtle Open in playground [ { "http://xmlns.com/foaf/0.1/name": [ { "@value": "Manu Sporny" } ], "http://xmlns.com/foaf/0.1/homepage": [ { "@id": "http://manu.sporny.org/" } ] } ]

JSON-LD's media type defines a profile parameter which can be used to signal or request expanded document form. The profile URI identifying expanded document form is http://www.w3.org/ns/json-ld#expanded.
