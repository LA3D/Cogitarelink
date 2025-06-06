Title: Security Vocabulary

URL Source: https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html

Markdown Content:
[Jump to Table of Contents](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#toc) [Pop Out Sidebar](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#toc)

Abstract
--------

This document describes the Security Vocabulary, i.e., the vocabulary used to ensure the authenticity and integrity of Verifiable Credentials and similar types of constrained digital documents using cryptography, especially through the use of digital signatures and related mathematical proofs .

Alternate versions of the vocabulary definition exist in [Turtle](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.ttl) and [JSON-LD](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.jsonld).

Published:

2025-03-25

Version Info:

2.0

See Also: [https://www.w3.org/TR/vc-data-integrity/](https://www.w3.org/TR/vc-data-integrity/)

Status of This Document
-----------------------

This document is merely a W3C\-internal document. It has no official standing of any kind and does not represent consensus of the W3C Membership.

Comments regarding this document are welcome. Please file issues directly on [GitHub](https://github.com/w3c/vc-data-integrity/issues/), or send them to [public-vc-comments@w3.org](mailto:public-vc-comments@w3.org) ([subscribe](mailto:public-vc-comments-request@w3.org?subject=subscribe), [archives](https://lists.w3.org/Archives/Public/public-vc-comments/)).

Table of Contents
-----------------

1.  [Abstract](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#abstract)
2.  [Status of This Document](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#sotd)
3.  [1\. Specification of terms](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#specification-of-terms)
4.  [2\. Namespaces](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#namespaces-0)
5.  [3\. `@context` files](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#context-files)
6.  [4\. Regular terms](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#term_definitions)
    1.  [4.1 Property definitions](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#property_definitions)
        1.  [4.1.1 `verificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#verificationMethod)
        2.  [4.1.2 `controller`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#controller)
        3.  [4.1.3 `proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proof)
        4.  [4.1.4 `domain`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#domain)
        5.  [4.1.5 `challenge`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#challenge)
        6.  [4.1.6 `previousProof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#previousProof)
        7.  [4.1.7 `proofPurpose`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proofPurpose)
        8.  [4.1.8 `proofValue`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proofValue)
        9.  [4.1.9 `created`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#created)
        10.  [4.1.10 `expiration`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#expiration)
        11.  [4.1.11 `nonce`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#nonce)
        12.  [4.1.12 `authentication`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#authentication)
        13.  [4.1.13 `assertionMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#assertionMethod)
        14.  [4.1.14 `capabilityDelegationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityDelegationMethod)
        15.  [4.1.15 `capabilityInvocationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityInvocationMethod)
        16.  [4.1.16 `keyAgreementMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#keyAgreementMethod)
        17.  [4.1.17 `cryptosuite`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#cryptosuite)
        18.  [4.1.18 `publicKeyMultibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#publicKeyMultibase)
        19.  [4.1.19 `secretKeyMultibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#secretKeyMultibase)
        20.  [4.1.20 `publicKeyJwk`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#publicKeyJwk)
        21.  [4.1.21 `secretKeyJwk`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#secretKeyJwk)
        22.  [4.1.22 `revoked`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#revoked)
        23.  [4.1.23 `digestMultibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#digestMultibase)
    2.  [4.2 Class definitions](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#class_definitions)
        1.  [4.2.1 `ControlledIdentifierDocument`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ControlledIdentifierDocument)
        2.  [4.2.2 `Proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Proof)
        3.  [4.2.3 `ProofGraph`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ProofGraph)
        4.  [4.2.4 `VerificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationMethod)
        5.  [4.2.5 `VerificationRelationship`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationRelationship)
        6.  [4.2.6 `DataIntegrityProof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#DataIntegrityProof)
        7.  [4.2.7 `Multikey`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Multikey)
        8.  [4.2.8 `JsonWebKey`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#JsonWebKey)
        9.  [4.2.9 `Ed25519VerificationKey2020`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Ed25519VerificationKey2020)
        10.  [4.2.10 `Ed25519Signature2020`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Ed25519Signature2020)
        11.  [4.2.11 `ProcessingError`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ProcessingError)
    3.  [4.3 Datatype definitions](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#datatype_definitions)
        1.  [4.3.1 `cryptosuiteString`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#cryptosuiteString)
        2.  [4.3.2 `multibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#multibase)
    4.  [4.4 Definitions for individuals](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#individual_definitions)
        1.  [4.4.1 `PROOF_GENERATION_ERROR`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#PROOF_GENERATION_ERROR)
        2.  [4.4.2 `PROOF_VERIFICATION_ERROR`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#PROOF_VERIFICATION_ERROR)
        3.  [4.4.3 `PROOF_TRANSFORMATION_ERROR`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#PROOF_TRANSFORMATION_ERROR)
        4.  [4.4.4 `INVALID_DOMAIN_ERROR`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#INVALID_DOMAIN_ERROR)
        5.  [4.4.5 `INVALID_CHALLENGE_ERROR`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#INVALID_CHALLENGE_ERROR)
        6.  [4.4.6 `INVALID_VERIFICATION_METHOD_URL`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#INVALID_VERIFICATION_METHOD_URL)
        7.  [4.4.7 `INVALID_CONTROLLED_IDENTIFIER_DOCUMENT_ID`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#INVALID_CONTROLLED_IDENTIFIER_DOCUMENT_ID)
        8.  [4.4.8 `INVALID_CONTROLLED_IDENTIFIER_DOCUMENT`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#INVALID_CONTROLLED_IDENTIFIER_DOCUMENT)
        9.  [4.4.9 `INVALID_VERIFICATION_METHOD`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#INVALID_VERIFICATION_METHOD)
        10.  [4.4.10 `INVALID_RELATIONSHIP_FOR_VERIFICATION_METHOD`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#INVALID_RELATIONSHIP_FOR_VERIFICATION_METHOD)
7.  [5\. Reserved terms](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#reserved_term_definitions)
    1.  [5.1 Reserved properties](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#reserved_property_definitions)
        1.  [5.1.1 `allowedAction`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#allowedAction)
        2.  [5.1.2 `capabilityChain`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityChain)
        3.  [5.1.3 `capabilityAction`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityAction)
        4.  [5.1.4 `caveat`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#caveat)
        5.  [5.1.5 `delegator`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#delegator)
        6.  [5.1.6 `invocationTarget`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#invocationTarget)
        7.  [5.1.7 `invoker`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#invoker)
8.  [6\. Deprecated terms](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#deprecated_term_definitions)
    1.  [6.1 Deprecated properties](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#deprecated_property_definitions)
        1.  [6.1.1 `blockchainAccountId`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#blockchainAccountId)
        2.  [6.1.2 `ethereumAddress`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ethereumAddress)
        3.  [6.1.3 `publicKeyBase58`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#publicKeyBase58)
        4.  [6.1.4 `publicKeyPem`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#publicKeyPem)
        5.  [6.1.5 `publicKeyHex`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#publicKeyHex)
        6.  [6.1.6 `jws`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#jws)
    2.  [6.2 Deprecated classes](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#deprecated_class_definitions)
        1.  [6.2.1 `Key`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Key)
        2.  [6.2.2 `EcdsaSecp256k1Signature2019`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#EcdsaSecp256k1Signature2019)
        3.  [6.2.3 `EcdsaSecp256k1Signature2020`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#EcdsaSecp256k1Signature2020)
        4.  [6.2.4 `EcdsaSecp256k1VerificationKey2019`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#EcdsaSecp256k1VerificationKey2019)
        5.  [6.2.5 `EcdsaSecp256k1RecoverySignature2020`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#EcdsaSecp256k1RecoverySignature2020)
        6.  [6.2.6 `EcdsaSecp256k1RecoveryMethod2020`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#EcdsaSecp256k1RecoveryMethod2020)
        7.  [6.2.7 `MerkleProof2019`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#MerkleProof2019)
        8.  [6.2.8 `X25519KeyAgreementKey2019`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#X25519KeyAgreementKey2019)
        9.  [6.2.9 `Ed25519VerificationKey2018`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Ed25519VerificationKey2018)
        10.  [6.2.10 `JsonWebKey2020`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#JsonWebKey2020)
        11.  [6.2.11 `JsonWebSignature2020`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#JsonWebSignature2020)
        12.  [6.2.12 `BbsBlsSignature2020`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#BbsBlsSignature2020)
        13.  [6.2.13 `BbsBlsSignatureProof2020`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#BbsBlsSignatureProof2020)
        14.  [6.2.14 `Bls12381G1Key2020`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Bls12381G1Key2020)
        15.  [6.2.15 `Bls12381G2Key2020`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Bls12381G2Key2020)
9.  [A. Diagram description](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#vocabulary-diagram-alt)
10.  [B. References](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#references)
    1.  [B.1 Informative references](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#informative-references)

In general, the terms — i.e., the properties and classes — used in the VCDM are formally specified in Recommendation Track documents published by the [W3C Verifiable Credentials Working Group](https://www.w3.org/groups/wg/vc) or, for some deprecated or reserved terms, in Reports published by the [W3C Credentials Community Group](https://www.w3.org/groups/cg/credentials). In each case of such external definition, the term's description in this document contains a link to the relevant specification. Additionally, the `rdfs:definedBy` property in the RDFS representation(s) refers to the formal specification.

In some cases, a local explanation is necessary to complement, or to replace, the definition found in an external specification. For instance, this is so when the term is needed to provide a consistent structure to the RDFS vocabulary, such as when the term defines a common supertype for class instances that are used as objects of specific properties, or when [RDF Graphs](https://www.w3.org/TR/rdf12-concepts/#section-rdf-graph) are involved. For such cases, the extra definition is included in the current document (and the `rdfs:comment` property is used to include them in the RDFS representations).

Graph containment

Graph con...

Class

Class

Property

Property

Superclass

Superclass

Domain

Domain

Range

Range

Datatype

Datatype

Type

Type[_controller_ controller](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#controller)[_revoked_ revoked](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#revoked)[_Ed25519VerificationKey2020_ Ed25519VerificationKey2020](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Ed25519VerificationKey2020)[_ProofGraph_ ProofGraph](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ProofGraph)[_proof_ proof](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proof)[_domain_ domain](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#domain)[_challenge_ challenge](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#challenge)[_previousProof_ previousProof](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#previousProof)[_proofPurpose _ proofPurpose](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proofPurpose)[_proofValue_ proofValue](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proofValue)[_expiration_ expiration](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#expiration)[_nonce_ nonce](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#nonce)[_created_ created](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#created)[_DataIntegrityProof_ DataIntegrityProof](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#DataIntegrityProof)[_Ed25519Signature2020_ Ed25519Signature2020](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Ed25519Signature2020)[_cryptosuite_ cryptosuite](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#cryptosuite)[cryptosuiteString cryptosuiteString](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#cryptosuiteString)[multibase multibase](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#multibase)[_Multikey_ Multikey](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Multikey)[_publicKeyMultibase_ publicKeyMultibase](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#publicKeyMultibase)[_secretKeyMultibase_ secretKeyMultibase](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#secretKeyMultibase)[_JsonWebKey_ JsonWebKey](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#JsonWebKey)

rdf:JSON

rdf:JSON[_secretKeyJwk_ secretKeyJwk](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#secretKeyJwk)[_publicKeyJwk_ publicKeyJwk](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#publicKeyJwk)[_digestMultibase_ digestMultibase](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#digestMultibase)[_VerificationRelationship_ VerificationRelationship](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationRelationship)[_verificationMethod_ verificationMethod](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#verificationMethod)[_authentication_ authentication](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#authentication)[_assertionMethod_ assertionMethod](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#assertionMethod)[_capabilityDelegationMethod_ capabilityDelegationMethod](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityDelegationMethod)[_capabilityInvocationMethod _ capabilityInvocationMethod](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityInvocationMethod)[_keyAgreementMethod_ keyAgreementMethod](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#keyAgreementMethod)[_VerificationMethod_ VerificationMethod](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationMethod)[_Proof_ Proof](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Proof)[_verificationMethod_ verificationMethod](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#verificationMethod)[_ControlledIdentifierDocument_ ControlledIdentifierDocument](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ControlledIdentifierDocument)

[Figure 1](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#vocabulary-diagram) Overview diagram of the vocabulary (without the reserved and deprecated items, error codes, and `xsd` datatypes).  
A separate, stand-alone [SVG version](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.svg) of the diagram, as well as a [textual description](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#vocabulary-diagram-alt), are also available.

This specification makes use of the following namespaces:

`sec`

`https://w3id.org/security#`

`cred`

`https://www.w3.org/2018/credentials#`

`dc`

`http://purl.org/dc/terms/`

`dcterms`

`http://purl.org/dc/terms/`

`owl`

`http://www.w3.org/2002/07/owl#`

`rdf`

`http://www.w3.org/1999/02/22-rdf-syntax-ns#`

`rdfs`

`http://www.w3.org/2000/01/rdf-schema#`

`xsd`

`http://www.w3.org/2001/XMLSchema#`

`vs`

`http://www.w3.org/2003/06/sw-vocab-status/ns#`

`schema`

`http://schema.org/`

`jsonld`

`http://www.w3.org/ns/json-ld#`

The following `@context` files make use of the terms defined in this specification:

*   [`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2)term list
    
    *   [`assertionMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#assertionMethod)
    *   [`authentication`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#authentication)
    *   [`capabilityDelegationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityDelegationMethod)
    *   [`capabilityInvocationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityInvocationMethod)
    *   [`challenge`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#challenge)
    *   [`created`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#created)
    *   [`cryptosuite`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#cryptosuite)
    *   [`cryptosuiteString`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#cryptosuiteString)
    *   [`domain`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#domain)
    *   [`expiration`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#expiration)
    *   [`keyAgreementMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#keyAgreementMethod)
    *   [`nonce`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#nonce)
    *   [`previousProof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#previousProof)
    *   [`proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proof)
    *   [`proofPurpose`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proofPurpose)
    *   [`proofValue`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proofValue)
    *   [`verificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#verificationMethod)
    
*   [`https://w3id.org/security/multikey/v1`](https://w3id.org/security/multikey/v1)term list
    
    *   [`Multikey`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Multikey)
    *   [`controller`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#controller)
    *   [`multibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#multibase)
    *   [`publicKeyMultibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#publicKeyMultibase)
    *   [`revoked`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#revoked)
    *   [`secretKeyMultibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#secretKeyMultibase)
    
*   [`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)term list
    
    *   [`JsonWebKey`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#JsonWebKey)
    *   [`Multikey`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Multikey)
    *   [`assertionMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#assertionMethod)
    *   [`authentication`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#authentication)
    *   [`capabilityDelegationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityDelegationMethod)
    *   [`capabilityInvocationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityInvocationMethod)
    *   [`controller`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#controller)
    *   [`expiration`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#expiration)
    *   [`keyAgreementMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#keyAgreementMethod)
    *   [`publicKeyJwk`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#publicKeyJwk)
    *   [`publicKeyMultibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#publicKeyMultibase)
    *   [`revoked`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#revoked)
    *   [`secretKeyJwk`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#secretKeyJwk)
    *   [`secretKeyMultibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#secretKeyMultibase)
    *   [`verificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#verificationMethod)
    
*   [`https://w3id.org/security/jwk/v1`](https://w3id.org/security/jwk/v1)term list
    
    *   [`JsonWebKey`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#JsonWebKey)
    *   [`controller`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#controller)
    *   [`publicKeyJwk`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#publicKeyJwk)
    *   [`revoked`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#revoked)
    *   [`secretKeyJwk`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#secretKeyJwk)
    
*   [`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2)term list
    
    *   [`assertionMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#assertionMethod)
    *   [`authentication`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#authentication)
    *   [`capabilityDelegationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityDelegationMethod)
    *   [`capabilityInvocationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityInvocationMethod)
    *   [`challenge`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#challenge)
    *   [`cryptosuite`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#cryptosuite)
    *   [`digestMultibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#digestMultibase)
    *   [`domain`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#domain)
    *   [`expiration`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#expiration)
    *   [`keyAgreementMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#keyAgreementMethod)
    *   [`nonce`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#nonce)
    *   [`previousProof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#previousProof)
    *   [`proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proof)
    *   [`proofPurpose`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proofPurpose)
    *   [`proofValue`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proofValue)
    *   [`verificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#verificationMethod)
    
*   [`https://www.w3.org/ns/did/v1`](https://www.w3.org/ns/did/v1)term list
    
    *   [`assertionMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#assertionMethod)
    *   [`authentication`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#authentication)
    *   [`capabilityDelegationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityDelegationMethod)
    *   [`capabilityInvocationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityInvocationMethod)
    *   [`controller`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#controller)
    *   [`keyAgreementMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#keyAgreementMethod)
    

The following are property definitions in the `sec` namespace.

_Verification method_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#dfn-verificationmethod).

See also:

[Decentralized Identifiers (DIDs) v1.0](https://www.w3.org/TR/did-core/#verification-methods)  

Range:

[`VerificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationMethod)

Relevant `@contexts`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2),  
[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)

_Controller_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#defn-controller).

The property's value should be a URL, i.e., not a literal.

Domain:

Union of:  
[`VerificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationMethod)  
[`ControlledIdentifierDocument`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ControlledIdentifierDocument)  

Relevant `@contexts`:

[`https://w3id.org/security/multikey/v1`](https://w3id.org/security/multikey/v1),  
[`https://w3id.org/security/jwk/v1`](https://w3id.org/security/jwk/v1),  
[`https://www.w3.org/ns/did/v1`](https://www.w3.org/ns/did/v1),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)

_Proof sets_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#proof-sets).

Range:

[`ProofGraph`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ProofGraph)

Relevant `@contexts`:

[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2),  
[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2)

_Domain of a proof_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#defn-domain).

Range:

[`xsd:string`](https://www.w3.org/2001/XMLSchema#string)

Domain:

[`Proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Proof)

Relevant `@contexts`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2),  
[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2)

_Challenge of a proof_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#defn-challenge).

Range:

[`xsd:string`](https://www.w3.org/2001/XMLSchema#string)

Domain:

[`Proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Proof)

Relevant `@contexts`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2),  
[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2)

_Previous proof_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#dfn-previousproof).

Range:

[`Proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Proof)

Domain:

[`Proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Proof)

Relevant `@contexts`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2),  
[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2)

_Proof purpose_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#dfn-proofpurpose).

Range:

[`VerificationRelationship`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationRelationship)

Domain:

[`Proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Proof)

Relevant `@contexts`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2),  
[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2)

_Proof value_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#dfn-proofvalue).

Range:

[`multibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#multibase)

Domain:

[`Proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Proof)

Relevant `@contexts`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2),  
[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2)

_Proof creation time_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#dfn-created).

Range:

`xsd:dateTime`

Domain:

[`Proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Proof)

Relevant `@context`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2)

_Expiration time for a proof or verification method_

See the formal definitions [here](https://www.w3.org/TR/vc-data-integrity/#defn-proof-expires) and [here](https://www.w3.org/TR/cid-1.0/#defn-vm-expires).

Historically, this property has often been expressed using `expires` as a shortened term in JSON-LD. Since this shortened term and its mapping to this property are in significant use in the ecosystem, the inconsistency between the short term name (`expires`) and the property identifier (`...#expiration`) is expected and should not trigger an error.

Range:

`xsd:dateTime`

Domain:

Union of:  
[`Proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Proof)  
[`VerificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationMethod)  

Relevant `@contexts`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2),  
[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)

_Nonce supplied by proof creator_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#dfn-nonce).

Range:

[`xsd:string`](https://www.w3.org/2001/XMLSchema#string)

Domain:

[`Proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Proof)

Relevant `@contexts`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2),  
[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2)

_Authentication method_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#authentication).

Type

[`VerificationRelationship`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationRelationship)  

Range:

[`VerificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationMethod)

Relevant `@contexts`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2),  
[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2),  
[`https://www.w3.org/ns/did/v1`](https://www.w3.org/ns/did/v1),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)

_Assertion method_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#assertion).

Type

[`VerificationRelationship`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationRelationship)  

Range:

[`VerificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationMethod)

Relevant `@contexts`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2),  
[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2),  
[`https://www.w3.org/ns/did/v1`](https://www.w3.org/ns/did/v1),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)

_Capability delegation method_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#capability-delegation).

Historically, this property has often been expressed using `capabilityDelegation` as a shortened term in JSON-LD. Since this shortened term and its mapping to this property are in significant use in the ecosystem, the inconsistency between the short term name (`capabilityDelegation`) and the property identifier (`...#capabilityDelegationMethod`) is expected and should not trigger an error.

Type

[`VerificationRelationship`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationRelationship)  

Range:

[`VerificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationMethod)

Relevant `@contexts`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2),  
[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2),  
[`https://www.w3.org/ns/did/v1`](https://www.w3.org/ns/did/v1),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)

_Capability invocation method_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#capability-invocation).

Historically, this property has often been expressed using `capabilityInvocation` as a shortened term in JSON-LD. Since this shortened term and its mapping to this property are in significant use in the ecosystem, the inconsistency between the short term name (`capabilityInvocation`) and the property identifier (`...#capabilityInvocationMethod`) is expected and should not trigger an error.

Type

[`VerificationRelationship`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationRelationship)  

Range:

[`VerificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationMethod)

Relevant `@contexts`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2),  
[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2),  
[`https://www.w3.org/ns/did/v1`](https://www.w3.org/ns/did/v1),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)

_Key agreement protocols_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#key-agreement).

Historically, this property has often been expressed using `keyAgreement` as a shortened term in JSON-LD. Since this shortened term and its mapping to this property are in significant use in the ecosystem, the inconsistency between the short term name (`keyAgreement`) and the property identifier (`...#keyAgreementMethod`) is expected and should not trigger an error.

Type

[`VerificationRelationship`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationRelationship)  

Range:

[`VerificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationMethod)

Relevant `@contexts`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2),  
[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2),  
[`https://www.w3.org/ns/did/v1`](https://www.w3.org/ns/did/v1),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)

_Cryptographic suite_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#dfn-cryptosuite).

Range:

[`cryptosuiteString`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#cryptosuiteString)

Domain:

[`DataIntegrityProof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#DataIntegrityProof)

Relevant `@contexts`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2),  
[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2)

_Public key multibase_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#dfn-publickeymultibase).

See also:

[multibase](https://datatracker.ietf.org/doc/html/draft-multiformats-multibase-03)  
[multicodec](https://github.com/multiformats/multicodec/blob/master/table.csv)  

Range:

[`multibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#multibase)

Domain:

[`Multikey`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Multikey)

Relevant `@contexts`:

[`https://w3id.org/security/multikey/v1`](https://w3id.org/security/multikey/v1),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)

_Secret key multibase_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#dfn-secretkeymultibase).

See also:

[multibase format](https://datatracker.ietf.org/doc/html/draft-multiformats-multibase-03)  
[multicodec format](https://github.com/multiformats/multicodec/blob/master/table.csv)  

Range:

[`multibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#multibase)

Domain:

[`Multikey`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Multikey)

Relevant `@contexts`:

[`https://w3id.org/security/multikey/v1`](https://w3id.org/security/multikey/v1),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)

_Public key JWK_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#dfn-publickeyjwk).

See also:

[IANA JOSE](https://www.iana.org/assignments/jose/jose.xhtml)  
[RFC 7517](https://tools.ietf.org/html/rfc7517)  

Range:

`rdf:JSON`

Domain:

[`JsonWebKey`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#JsonWebKey)

Relevant `@contexts`:

[`https://w3id.org/security/jwk/v1`](https://w3id.org/security/jwk/v1),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)

_Secret key JWK_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#dfn-secretkeyjwk).

See also:

[IANA JOSE](https://www.iana.org/assignments/jose/jose.xhtml)  
[RFC 7517](https://tools.ietf.org/html/rfc7517)  

Range:

`rdf:JSON`

Domain:

[`JsonWebKey`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#JsonWebKey)

Relevant `@contexts`:

[`https://w3id.org/security/jwk/v1`](https://w3id.org/security/jwk/v1),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)

_Revocation time_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#dfn-revoked).

Range:

`xsd:dateTime`

Domain:

[`VerificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationMethod)

Relevant `@contexts`:

[`https://w3id.org/security/jwk/v1`](https://w3id.org/security/jwk/v1),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1),  
[`https://w3id.org/security/multikey/v1`](https://w3id.org/security/multikey/v1)

_Digest multibase_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#dfn-digestmultibase).

**_(Feature at Risk)_** The Working Group is currently attempting to determine whether cryptographic hash expression formats can be unified across all of the VCWG core specifications. Candidates for this mechanism include `digestSRI` and `digestMultibase`.

Range:

[`multibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#multibase)

Relevant `@context`:

[`https://www.w3.org/ns/credentials/v2`](https://www.w3.org/ns/credentials/v2)

The following are class definitions in the `sec` namespace.

_Controlled Identifier Document_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#controlled-identifier-documents).

In the domain of:

[`controller`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#controller)

_Digital proof_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#dfn-data-integrity-proof).

This class represents a digital proof on serialized data.

Range of:

[`previousProof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#previousProof)

Domain of:

[`domain`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#domain), [`challenge`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#challenge), [`previousProof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#previousProof), [`proofPurpose`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proofPurpose), [`proofValue`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proofValue), [`created`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#created), [`nonce`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#nonce)

In the domain of:

[`expiration`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#expiration)

_An RDF Graph for a digital proof_

Instances of this class are [RDF Graphs](https://www.w3.org/TR/rdf11-concepts/#section-rdf-graph) \[[RDF11-CONCEPTS](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#bib-rdf11-concepts "RDF 1.1 Concepts and Abstract Syntax")\], where each of these graphs must include exactly one [Proof](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Proof) instance.

Range of:

[`proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proof)

_Verification method_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#verification-methods).

Instances of this class must be [denoted by URLs](https://www.w3.org/TR/rdf11-concepts/#resources-and-statements), i.e., they cannot be blank nodes.

Range of:

[`verificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#verificationMethod), [`authentication`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#authentication), [`assertionMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#assertionMethod), [`capabilityDelegationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityDelegationMethod), [`capabilityInvocationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#capabilityInvocationMethod), [`keyAgreementMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#keyAgreementMethod)

Domain of:

[`revoked`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#revoked)

In the domain of:

[`controller`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#controller), [`expiration`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#expiration)

_Verification relationship_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#verification-relationships).

Instances of this class are verification relationships like, for example, [authentication](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#authentication) or [assertionMethod](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#assertionMethod). These resources can also appear as values of the [proofPurpose](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proofPurpose) property.

Subclass of:

[`rdf:Property`](https://www.w3.org/1999/02/22-rdf-syntax-ns#Property)

Range of:

[`proofPurpose`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proofPurpose)

_A Data Integrity Proof_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#dataintegrityproof).

Subclass of:

[`Proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Proof)

Domain of:

[`cryptosuite`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#cryptosuite)

_Multikey Verification Method_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#multikey).

See also:

[EdDSA Cryptosuites](https://www.w3.org/TR/vc-di-eddsa/#multikey)  
[ECDSA Cryptosuites](https://www.w3.org/TR/vc-di-ecdsa/#multikey)  
[BBS Cryptosuites](https://www.w3.org/TR/vc-di-bbs/#multikey)  

Subclass of:

[`VerificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationMethod)

Domain of:

[`publicKeyMultibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#publicKeyMultibase), [`secretKeyMultibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#secretKeyMultibase)

Relevant `@contexts`:

[`https://w3id.org/security/multikey/v1`](https://w3id.org/security/multikey/v1),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)

_JSON Web Key Verification Method_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#jsonwebkey).

Subclass of:

[`VerificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationMethod)

Domain of:

[`publicKeyJwk`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#publicKeyJwk), [`secretKeyJwk`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#secretKeyJwk)

Relevant `@contexts`:

[`https://w3id.org/security/jwk/v1`](https://w3id.org/security/jwk/v1),  
[`https://www.w3.org/ns/cid/v1`](https://www.w3.org/ns/cid/v1)

_ED2559 Verification Key, 2020 version_

See the [formal definition of the term](https://www.w3.org/TR/vc-di-eddsa/#ed25519verificationkey2020).

Subclass of:

[`VerificationMethod`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#VerificationMethod)

_Ed25519 Signature Suite, 2020 version_

See the [formal definition of the term](https://www.w3.org/TR/vc-di-eddsa/#ed25519signature2020).

Subclass of:

[`Proof`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Proof)

_Processing error_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#processing-errors).

The following are datatype definitions in the `sec` namespace.

_Datatype for cryptosuite Identifiers_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#cryptosuiteString).

Derived from:

[`xsd:string`](https://www.w3.org/2001/XMLSchema#string)

Range of:

[`cryptosuite`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#cryptosuite)

Relevant `@context`:

[`https://w3id.org/security/data-integrity/v2`](https://w3id.org/security/data-integrity/v2)

_Datatype for multibase values_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#multibase).

Derived from:

[`xsd:string`](https://www.w3.org/2001/XMLSchema#string)

Range of:

[`proofValue`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#proofValue), [`publicKeyMultibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#publicKeyMultibase), [`secretKeyMultibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#secretKeyMultibase), [`digestMultibase`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#digestMultibase)

Relevant `@context`:

[`https://w3id.org/security/multikey/v1`](https://w3id.org/security/multikey/v1)

The following are definitions for individuals in the `sec` namespace.

_Proof generation error_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#PROOF_GENERATION_ERROR).

Type

[`ProcessingError`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ProcessingError)  

_Malformed proof_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#PROOF_VERIFICATION_ERROR).

Type

[`ProcessingError`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ProcessingError)  

_Mismatched proof purpose_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#PROOF_TRANSFORMATION_ERROR).

Type

[`ProcessingError`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ProcessingError)  

_Invalid proof domain_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#INVALID_DOMAIN_ERROR).

Type

[`ProcessingError`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ProcessingError)  

_Invalid challenge_

See the [formal definition of the term](https://www.w3.org/TR/vc-data-integrity/#INVALID_CHALLENGE_ERROR).

Type

[`ProcessingError`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ProcessingError)  

_Invalid verification method URL_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#INVALID_VERIFICATION_METHOD_URL).

Type

[`ProcessingError`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ProcessingError)  

_Invalid controlled identifier document id_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#INVALID_CONTROLLED_IDENTIFIER_DOCUMENT_ID).

Type

[`ProcessingError`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ProcessingError)  

_Invalid controlled identifier document_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#INVALID_CONTROLLED_IDENTIFIER_DOCUMENT).

Type

[`ProcessingError`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ProcessingError)  

_Invalid verification method_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#INVALID_VERIFICATION_METHOD).

Type

[`ProcessingError`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ProcessingError)  

_Invalid relationship for verification method_

See the [formal definition of the term](https://www.w3.org/TR/cid-1.0/#INVALID_RELATIONSHIP_FOR_VERIFICATION_METHOD).

Type

[`ProcessingError`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#ProcessingError)  

All terms in this section are _**reserved**_. Implementers may use these properties, but should expect them and/or their meanings to change during the process to normatively specify them.

The following are _**reserved**_ property definitions in the `sec` namespace.

_Allowed action_ _(reserved)_

See the [formal definition of the term](https://w3c-ccg.github.io/zcap-spec/#delegated-capability).

_Capability chain_ _(reserved)_

See the [formal definition of the term](https://w3c-ccg.github.io/zcap-spec/#delegation).

_Capability action_ _(reserved)_

See the [formal definition of the term](https://w3c-ccg.github.io/zcap-spec/#invoking-root-capability).

_Caveat_ _(reserved)_

See the [formal definition of the term](https://w3c-ccg.github.io/zcap-spec/#caveats).

_Delegator_ _(reserved)_

See the [formal definition of the term](https://w3c-ccg.github.io/zcap-spec/#delegation).

_Invocation target_ _(reserved)_

See the [formal definition of the term](https://w3c-ccg.github.io/zcap-spec/#root-capability).

_Invoker_ _(reserved)_

See the [formal definition of the term](https://w3c-ccg.github.io/zcap-spec/#invocation).

All terms in this section are _**deprecated**_, and are only kept in this vocabulary for backward compatibility.

New applications should not use them.

The following are _**deprecated**_ property definitions in the `sec` namespace.

_Blockchain account ID_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/security-vocab/#blockchainAccountId).

Range:

[`xsd:string`](https://www.w3.org/2001/XMLSchema#string)

_Ethereum address_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/security-vocab/#ethereumAddress).

See also:

[EIP-55](https://eips.ethereum.org/EIPS/eip-55)  
[Ethereum Yellow Paper: Ethereum: a secure decentralised generalised transaction ledger](https://ethereum.github.io/yellowpaper/paper.pdf)  

Range:

[`xsd:string`](https://www.w3.org/2001/XMLSchema#string)

_Base58-encoded Public Key_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/security-vocab/#publicKeyBase58).

Range:

[`xsd:string`](https://www.w3.org/2001/XMLSchema#string)

_Public key PEM_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/security-vocab/#publicKeyPem).

Range:

[`xsd:string`](https://www.w3.org/2001/XMLSchema#string)

_Hex-encoded version of public Key_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/security-vocab/#publicKeyHex).

See also:

[rfc4648](https://tools.ietf.org/html/rfc4648#section-8)  

Range:

[`xsd:string`](https://www.w3.org/2001/XMLSchema#string)

_Json Web Signature_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/security-vocab/#jws).

See also:

[Detached JSON Web Signature](https://tools.ietf.org/html/rfc7797)  

The following are _**deprecated**_ class definitions in the `sec` namespace.

_Cryptographic key_ _(deprecated)_

This class represents a cryptographic key that may be used for encryption, decryption, or digitally signing data. This class serves as a supertype for specific key types.

_ecdsa-sep256k1, 2019 version_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/ld-cryptosuite-registry/#ecdsa-secp256k1).

_ecdsa-sep256k1, 2020 version_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/ld-cryptosuite-registry/#ecdsa-secp256k1).

_ecdsa-secp256k1 verification key, 2019 version_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/ld-cryptosuite-registry/#ecdsasecp256k1recoverysignature2020).

Subclass of:

[`Key`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#Key)

_ecdsa-secp256k1 recovery signature, 2020 version_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/ld-cryptosuite-registry/#ecdsasecp256k1recoverysignature2020).

_ecdsa-secp256k1 recovery method, 2020 version_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/ld-cryptosuite-registry/#ecdsasecp256k1recoverymethod2020).

_Merkle Proof_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/lds-merkle-proof-2019/).

_X25519 Key Agreement Key, 2019 version_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/security-vocab/#X25519KeyAgreementKey2019).

_ED2559 Verification Key, 2018 version_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/ld-cryptosuite-registry/#ed25519).

_JSON Web Key, 2020 version_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/security-vocab/#JsonWebKey2020).

A linked data proof suite verification method type used with [`JsonWebSignature2020`](https://www.w3.org/2025/credentials/vcdi/vocab/v2/vocabulary.html#JsonWebSignature2020)

_JSON Web Signature, 2020 version_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/security-vocab/#JsonWebSignature2020).

_BBS Signature, 2020 version_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/security-vocab/#BbsBlsSignature2020).

_BBS Signature Proof, 2020 version_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/security-vocab/#BbsBlsSignatureProof2020).

_BLS 12381 G1 Signature Key, 2020 version_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/security-vocab/#Bls12381G1Key2020).

_BLS 12381 G2 Signature Key, 2020 version_ _(deprecated)_

See the [formal definition of the term](https://w3c-ccg.github.io/security-vocab/#Bls12381G2Key2020).

Overview diagram of the vocabulary (without the reserved and deprecated items, error codes, and `xsd` datatypes).The diagram uses boxes, ellipses, and connecting lines with different "styles" (border color, end marker, line type) to differentiate their semantic meaning: "Property", "Class", and "Datatype" are identified by the shape of the graph node (e.g., an ellipse signifies a "Class"); "Superclass", "Domain Of", "Range", "Type", and "Contains" relationships are identified by the style of the connecting line. These style names are used in the explanation text that follows, below.

The diagram is roughly divided into three sections — lower left, lower right, and upper. To make this description easier to understand, these sections will be respectively referred to as the "Proof", "Verification Method", and "Verification Relationship" sections. Shapes in the three sections are connected by lines of different styles; additionally, one box, labeled as "multibase" and shaped as "Datatype", bridges the two lower sections ("Proof" and "Verification Method").

Each of these sections has an ellipse at the top, labeled as "Proof", "VerificationMethod", and "VerificationRelationship", respectively. The Verification Method section includes an additional ellipse, labeled as "ControllerDocument", side-by-side with the ellipse labeled as "VerificationMethod".

The left side of the section contains another ellipse, labeled as "ProofGraph", and connected with a line styled as "Contains" to the "Proof" ellipse. A separate box, styled as "Property" and labeled as "proof", is connected with a line styled as "Range" to the "ProofGraph" ellipse.

There are two more ellipses in this section, labeled as "Ed25519Signature2020" and "DataIntegrityProof", and each connected to the "Proof" ellipse with lines styled as "Superclass". The "DataIntegrityProof" ellipse is also connected to a box, styled as "Property" and labeled as "cryptosuite", with a line styled as "Domain Of". The "cryptosuite" Property box is connected to a shape, styled as "Datatype" and labeled as "cryptosuiteString", with a line styled as "Range".

The right side of the section contains a column of labeled boxes, all styled as "Property". The labels, from top to bottom, are "previousProof", "domain", "challenge", "nonce", "created", and "proofValue". The "Proof" ellipse is connected to all of these boxes with lines styled as "Domain Of". The "previousProof" box is also connected to the "Proof" ellipse, with a line styled as "Range". The "proofValue" box is connected to a shape, styled as "Datatype" and labeled as "multibase", with a line styled as "Range". Finally, the same "multibase" "Datatype" shape is connected to another box, styled as "Property" and labeled as "digestMultibase", with a line styled as "Range".

The left side of this section contains a column of three labeled boxes, all styled as "Property". The labels, from top to bottom, are "controller", "expires", and "revoked". Each of these is connected to the "VerificationMethod" ellipse, with a line styled as "Domain Of". The "controller" "Property" box is also connected to the "ControllerDocument" ellipse, while the "expires" "Property" box is also connected to the "Proof" ellipse (in the Proof section); both of these extra connecting lines are styled as "Domain Of".

There is also a distinct box, styled as "Property" and labeled as "verificationMethod". This "verificationMethod" box is connected to the "VerificationMethod" ellipse, with a connecting line styled as "Range".

The middle of this section contains three more ellipses, labeled as "Multikey, "Ed25519VerificationKey2020", and "JsonWebKey". Each of these is connected to the "VerificationMethod" ellipse, with a line styled as "Superclass".

Two boxes, styled as "Property" and labeled as "secretKeyMultibase" and "publicKeyMultibase", are connected to the ellipse labeled as "Multikey" with a line styled as "Domain Of". Each of these boxes is also connected to the "multibase" "Datatype" shape in the Proof section, with lines styled as "Range".

Finally, two boxes, styled as "Property" and labeled as "secretKeyJwk" and "publicKeyJwk", are connected to the "JsonWebKey" ellipse, with a line styled as "Domain Of". Both boxes are also connected to a shape, styled as "Datatype" and labeled as "rdf:JSON", with lines styled as "Range".

The left side of the section contains a single box, styled as "Property" and labeled as "proofPurpose". This box is connected to the "VerificationRelationship" ellipse, with a line styled as "Range". It is also connected to the "Proof" ellipse in the Proof section, with a line styled as "Domain Of".

The right side of the section contains a column of labeled boxes, all styled as "Property". The labels, from top to bottom, are "verificationMethod", "authentication", "assertionMethod", "capabilityDelegation", "capabilityInvocation", and "keyAgreement". Each of these boxes is connected to the "VerificationMethod" ellipse in the Verification Method section, with a line styled as "Range". Finally, each of these boxes is also connected to the "VerificationRelationship" ellipse, with a line styled as "Type".

\[RDF11-CONCEPTS\]

[RDF 1.1 Concepts and Abstract Syntax](https://www.w3.org/TR/rdf11-concepts/). Richard Cyganiak; David Wood; Markus Lanthaler. W3C. 25 February 2014. W3C Recommendation. URL: [https://www.w3.org/TR/rdf11-concepts/](https://www.w3.org/TR/rdf11-concepts/)