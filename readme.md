* ReBAC instead of RBAC and ABAC
* Namespace
* tuples
* relations b/w users and objects -> owner, editor, commenter, and viewer.
* set operations for access
* Access Control Language(ACL) form -> "user U has relation R to object O"
* check("does user U have relation R to object O")
* group membership -> the object property is a group and the relation is semantically equivalent to member.  Groups can contain other groups
* For groups -> recursively traverse a hierarchy of group memberships

## Relation Tuples (Core of the ReBAC -> Relationship-Based Access Control)
⟨tuple⟩ ::= ⟨object⟩‘#’⟨relation⟩‘@’⟨user⟩
⟨object⟩ ::= ⟨namespace⟩‘:’⟨object id⟩
⟨user⟩ ::= ⟨user id⟩ | ⟨userset⟩
⟨userset⟩ ::= ⟨object⟩‘#’⟨relation⟩

* namespace⟩ , ⟨relation⟩ are predefined in client configurations
* ⟨object id⟩ is a string, and ⟨user id⟩ is an integer
* Primary keys for identifying the tuple =  ⟨namespace⟩, ⟨object id⟩, ⟨relation⟩, and ⟨user⟩

* example of a single recrod
`doc:readme#owner@10 => User 10 is an owner of doc:readme`

* example of userset
We define the group relation
`document:doc1#viewer@group:team1#member => team1 has viewer access on document:doc1`

To identify the members we have these records in the db
`group:team1#member@user:alice => alice is member of team1`
`group:team1#member@user:bob = bob is member of team1`

## New enemy problem(respecting the order of the actions and ACL)
### Problem
* The zanzibar system is a distributed system.
* If all datasource is not updated it may result in wrong result
* Example
1. Bob initially has access to a folder (folder1).
2. Alice removes Bob from the ACL of folder1 at T1.
3. Alice asks Charlie to move a new document (doc1) into folder1 at T2.
Now Bob should not be able to access or view the new documents. 
But when it may fail?
* At T3, Bob’s read request went to a replica that hadn't received the ACL update from T1 yet.
* So, it incorrectly returned an old ACL where Bob still had access.
* Bob can now see doc1 even though he was removed before it was added.
> Primarily due to distributed systems as data needs to replicated across all replicas.

### Solutions

#### Google spanner
> Google spanner for both external consistency and sanpshot reads
* It leverages the google spanner which is highly consistent. Spanner leverages TrueTime for maintaining its consistency principle, ensuring that during transaction commits, the time is accurately captured.
Basically this is mentioned as **external consistency** in the paper.

* External consistency means that Zanzibar ensures that updates to ACLs and content respect real-world causal ordering by using timestamps assigned by **Spanner’s TrueTime mechanism**.

* Application
When an ACL update occurs, Spanner assigns a TrueTime timestamp.
If ACL update X precedes Y, then it ensures:
Tx < Ty 

Any snapshot read at timestamp T will see all updates ≤ T and none after.
This guarantees causal ordering is respected, even in a distributed system.

* What is snapshot here?
In simple terms, it is the aggregated result of all updates up to a given timestamp T. Basically it gives the latest state of that entity.
Or we can say **precomputed ACL snapshots** or **timestamped views of ACLs**

We get ->
1. Performance
2. Consistency

This snapshot reflects the state of access control lists (ACLs) and other relevant data up to that timestamp, ensuring that the checks are consistent and reflect all updates that occurred before that time

#### Zookie protocol
> Zookie is an opaque consistency token that maintains a global timestamp to ensure ACL checks respect causal ordering. It is returned after a write
* Each write operation generates a unique identifier called a "zookie" which includes a timestamp. And client receives that
Example
1. Before Alice adds the new document, she gets a Zookie at T2.
2. The Zookie is stored with the document metadata.
3. Any ACL check on the document must use a snapshot at ≥ T2.
4. Since Bob was already removed at T1, he correctly does not have access.

## Namespace Configuration
Zanzibar handles modeling with namespace configurations. A namespace configuration in Zanzibar is a set of rules that define how resources within a specific namespace can be accessed. Such as a collection of databases or a set of virtual machines.

### Relation Configs and Userset Rewrites
Sometimes clients have relations in hierarchical fashion where a single tuple will not define every permissions.
Ex -> editor has permission for viewer as well.
Plus they can't static as well as they are more of the client side things.
For every editor, storing another tuple viewer for each editor is wastage of storage.

So, clients define **object-agnostic relationships** via **userset rewrite rules** in relation configs.

Example

Namespace configuration with concentric relations on documents.
1. All owners are editors, 
2. all editors are viewers. 
3. viewers of the parent folder are also viewers of the document.
    ```
    name: "doc"
    relation { name: "owner" }

    relation {
        name: "editor"
        userset_rewrite {
        union {
            child { _this {} }
            child { computed_userset { relation: "owner" } }
            }
        } 
    }

    relation {
        name: "viewer"
        userset_rewrite {
            union {
                child { _this {} }
                child { computed_userset { relation: "editor" } }
                child { tuple_to_userset {
                    tupleset { relation: "parent" }
                    computed_userset {
                        object: $TUPLE_USERSET_OBJECT # parent folder
                        relation: "viewer"
                    } 
                } 
            }
    } } }
    ```
#### How it works?
Userset rewrite rules are defined per relation in a namespace.
1. _this: Returns all the users having the realtion. It is default one when no userset_rewrite is given
2. computed userset: Inherit users from another relation on the same object.
3. tuple_to_userset: Inherit users from related objects (e.g., parent folder’s viewers).
4. Logical Operators (union, intersection, difference) → Combine multiple usersets.

> It can be nested as well for complex permissions

## API
> Zookie is used here for all api methods

### Read
1. Display ACLs or group memberships (e.g., showing a list of users who can edit a file).
2. Prepare for a subsequent write (e.g., checking existing permissions before modifying them).
3. Lookup access control entries (e.g., fetching all users with "viewer" permission on a document).

#### Payload
1. Tuplesets → Define what relation tuples to fetch.
2. Optional Zookie → Ensures consistency across reads and writes.

3. Without a Zookie → Zanzibar chooses a recent snapshot (fast, but might not reflect the latest writes).

4. With a Zookie from a previous write → Ensures read results are at least as new as that write(zookie is pointing at).

5. With a Zookie from a previous read → Ensures the same ACL view as the previous read.

### Write(update,delete)
#### Problem
1. Multiple clients may try to modify the same ACL at the same time.
2. If two users are trying to edit permissions on the same file, we need a way to avoid conflicts.

#### Solution
> optimistic concurrency implemented with a lock tuple instead of version numbering
Uses read-modify-write process with optimistic concurrency

1. Read all relation tuples of an object, including a perobject “lock” tuple.
* A special lock tuple that is used to detect concurrent modifications.
* The "lock" tuple (File_X, lock, lock_marker_123) is a special entry that helps detect concurrent writes.

2. Generate the tuples to write or delete. Send the writes,
along with a touch on the lock tuple, to Zanzibar, with
the condition that the writes will be committed only if
the lock tuple has not been modified since the read.

3. If the write condition is not met, go back to step 1.
The lock tuple is just a regular relation tuple used by
clients to detect write races.

### Watch
> Realtime incremental updates
1. The Watch API listens for changes to relation tuples.
2. When a permission changes (e.g., a user is added or removed from a document), Zanzibar sends an event with a timestamp.
3. The client updates its index using this event, keeping it synchronized without re-fetching everything.

Example
> The secondary index is local—it lives on the client’s side, in a database, cache, or in-memory store, separate from Zanzibar.
* Let's say a system like Google Drive maintains an index of which users have access to which files.
* Whenever anything is updated the subsribers to the watcher, will be updated. They can manipulate their own index instead of querying the zanzibar everytime.
* Every time user A wants to see which documents they can edit, the system queries Zanzibar.
* If thousands of users do this simultaneously, it puts high load on Zanzibar.
* When user:A logs in, instead of querying Zanzibar, the system fetches results from this index instantly.

### Check
> Doesn't reflect rewrite rules. If asked for viewer tuples, it will not return tuple with owner relation

1. normal check
* userset. ex  -> doc:123#viewer (Checking if the user can view document 123)
* putative user -> The user requesting access
* zookie ->  A snapshot identifier that ensures the check is evaluated at a consistent version of the ACL (Access Control List). Getting latest permission

2. Content change checks
* This is a special type of authorization check **used before modifying content**.

* Basically no zookie is send by the client for checking whether current user has the access or not

* If it has access(zanzibar check by latest snapshot), a new zookie is returned having timestamp is greater than or equal to any ACL updates that affected this modification.

### Expand
* For getting effective userset for a given relation
* Resolves all users who have access both directly or indirectly.
* Returns a user tree. t constructs a tree structure based on userset rules. Not a direct flat list

* Example: Expanding Access to doc:123#viewer

Scenario
1. User Alice is explicitly a viewer (doc:123#viewer).
2. Group Editors also has viewer access (doc:123#viewer -> group:Editors#member).
3. Bob is a member of Editors.
```json
{
  "object": "doc:123",
  "relation": "viewer",
  "userset": {
    "union": [
      {
        "type": "user",
        "id": "Alice"
      },
      {
        "type": "group",
        "id": "Editors",
        "relation": "member",
        "userset": {
          "union": [
            {
              "type": "user",
              "id": "Bob"
            }
          ]
        }
      }
    ]
  }
}
```

1. "object": "doc:123" → The document being accessed.
2. "relation": "viewer" → The relation we are expanding.
3. "userset" → The users and groups who have access.
4. Union (or) →
    * Direct user: Alice has direct access.
    * Group access: The group "Editors" has access through "member".
    * Nested userset: Bob is part of "Editors", so he also gets access.

## Architecture
### Aclservers
These servers handle client requests for checking, reading, expanding, and writing ACLs. They interact with the Spanner database to retrieve and update ACL information.

### Watch servers
* watchservers are a specialized server type that respond to Watch requests. They tail the changelog and serve a stream of namespace changes to clients in near real time
* Tailing the Changelog

    1. A changelog is a log of all updates (CRUD operations) to relation tuples in Zanzibar.
    2. "Tailing" means continuously reading the latest entries from this log as they are written (like tail -f in Linux).
    3. The WatchServer follows this log to detect changes as soon as they happen.
* Serving a Stream of Namespace Changes

    1. When an update occurs (e.g., a user is added to a group, a permission is revoked, etc.), the WatchServer captures that change.
    2. It then streams these changes to clients that have subscribed to updates for a particular namespace (e.g., all changes in document#viewer).
    3. This allows clients to keep local caches up-to-date instead of re-fetching data.
* Append only changelogs (transforming changelog to relations)
    > An append-only log is like a diary where you can only write new entries, never erase or modify the old ones. It's a data structure that stores records in a linear sequence, always adding new data at the end.
    1. Structure of a changelog:
        * Timestamp (when the change happened)
        * Operation (ADD or REMOVE)
        * Object, Relation, and User (what changed)
        * Zookie (Snapshot Token) (to ensure consistency)
    2. Translation of logs to relations
        * Read the tail of changelog(new entries)
        * Extract properties from the structure
        * Updating the Userset Tree
            * Zanzibar stores relations as a userset tree, where each object#relation maps to a list of users or other usersets.
            * If the operation is ADD, the user is inserted into the userset.
            * If the operation is REMOVE, the user is deleted.
        * the userset tree is not stored explicitly as a separate data structure. Instead, it is computed dynamically using a combination of a database (Spanner) and a caching layer (Leopard)

### Leopard Indexing System
* Leopard is an indexing system used to optimize operations on large and deeply nested sets. 
* It reads periodic snapshots of ACL data and watches for changes between snapshots. 
* It performs transformations on that data, such as denormalization, and responds to requests from aclservers

## Storage
* Relation tuples of each namespace in a separate database, where each row is identified by primary key
* Multiple tuple versions are stored on different rows, so that we
can evaluate checks and reads at any timestamp within the
garbage collection window