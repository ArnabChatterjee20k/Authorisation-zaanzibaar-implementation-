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
5. Zookies -> hashing. Every write sends a zookie with a timestamp which will be required for reading.
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
    body -> {
        object:string,
        relation:string
        resource: string,
    }