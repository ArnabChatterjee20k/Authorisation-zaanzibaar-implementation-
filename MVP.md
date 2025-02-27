### MVP
✅ Store & Retrieve Relation Tuples (⟨object ID, relation, user⟩)
✅ Basic Read API – Fetch all users who have access to an object
✅ Check API – Verify if a specific user has a relation to an object
✅ Expand API – Resolve indirect usersets (groups)
✅ Watch API – Track changes for updates
https://chatgpt.com/share/67bb56bc-59fc-8011-b064-672c8f29b2ae

### Services
1. Storage -> Postgresql
2. Caching -> redis with ttl
3. Leopard indexing system -> Postgres table with materialised views with refreshing with pg_cron for pre computation at specific timestamps
4. Consistency -> Transactions
[X] Zookies -> hashing. Every write sends a zookie with a timestamp which will be required for reading.
6. watch servers -> ??

### Core features
1. check
2. write
2. write
3. read -> zookie requirement is mandatory
4. expand
6. watch
7. tenancy for multiple clients

### Flow
1. client will first register itself  first for getting api key
2. Enfore rules like to have hierachical userset rewrites
3. write(can be recursive)
    required -> api key
    body -> {
        object:string,
        relation:string
        resource: string,
    }
    response -> zookietoken(hash+id)

4. check(can be recursive)
    required -> zookie token , api token
    body -> tuples{
        object:string,
        relation:string
        resource: string,
    }

### Building the write layer
* Everything is permission 
* For every action I need to set up relationship.
* If i move a folder1 from a to b we need to change a parent to b parent

### Building the check layer
* Recursive
* document:doc1#viewer@group:team1#member => ⟨object⟩‘#’⟨relation⟩‘@’⟨user⟩
    * object = document:doc1 => ⟨namespace⟩:⟨object id⟩
        * namespace = document
        * objectId = doc1
    * relation = viewer
    * user = group:team1#member = ⟨object⟩‘#’⟨relation⟩‘@’⟨user⟩
        * object = group:team1 => => ⟨namespace⟩:⟨object id⟩
            * namespace = group
            * objectId = team1
        * relation = member
        * user = not present
    * final check(member of group:team1 is viewer of document:doc1)
    > We can go more deep if present

* ultimate params => namespace, objectId, relation, userId => each layer segregated by #,@,:
* given check("userId1","viewer","document:doc1")
* checking order 
    * document:doc1#viewer@group:team1#member
    * so group:team1#member has access of "viewer"
    * check("userId1","member","groupd:team1")
    * if yes => true alse false

* so we need to have the indexed document laying out all the relation a namespace is having
otherwise each recusive check gonna take time
* using indexing-system for precomputed indexes.
    ```json
        {
             "document:doc1#viewer": ["group:team1#member"],
            "group:team1#member": ["user:userId1", "user:userId2"]
        }
    ```