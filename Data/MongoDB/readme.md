# MongoDB

> [!NOTE]
> **Status**: In Progress

---

## Architecture

```mermaid
graph LR
    A[Database] --> B[Collection]
    B --> C[Document]
    C --> D[Key:Value Pairs]
```

---

## Core Concepts

<table>
<thead>
<tr><th>Concept</th><th>Description</th><th>Details</th></tr>
</thead>
<tbody>

<tr>
<td><strong>Collection</strong></td>
<td>Group of documents (like a table)</td>
<td></td>
</tr>

<tr>
<td><strong>Document</strong></td>
<td>JSON-like record (BSON format)</td>
<td></td>
</tr>

<tr>
<td><strong>Index</strong></td>
<td>Improves query performance</td>
<td></td>
</tr>

<tr>
<td><strong>Commands</strong></td>
<td>CRUD + utility operations</td>
<td>
<details><summary>Show</summary>

<b>Insert</b>

```js
db.col.insertOne({ key: "value" })
db.col.insertMany([{ key: "value" }, { key: "value2" }])
```

<b>Find</b>

```js
db.col.find({ key: "value" })       // all matches
db.col.findOne({ key: "value" })    // first match
```

<b>Update</b>

```js
db.col.updateOne({ key: "value" }, { $set: { key: "new" } })
db.col.updateMany({ key: "value" }, { $set: { key: "new" } })
```

<b>Delete</b>

```js
db.col.deleteOne({ key: "value" })
db.col.deleteMany({ key: "value" })
```

<b>Sort, Limit & Skip</b>

```js
db.col.find().sort({ field: 1 })    // 1 = asc, -1 = desc
db.col.find().limit(10)
db.col.find().skip(5).limit(10)     // pagination
```

<b>Count & Distinct</b>

```js
db.col.countDocuments({ key: "value" })
db.col.distinct("field")
```

</details>
</td>
</tr>

<tr>
<td><strong>Query Operators</strong></td>
<td>Modify / check field values</td>
<td>
<details><summary>Show</summary>

| Operator | Description |
|---|---|
| `$set` | Set a field value |
| `$unset` | Remove a field |
| `$exists` | Check field existence |
| `$ne` | Not equal |
| `$lt` / `$lte` | Less than / less than or equal |
| `$in` / `$nin` | Match / not match values in array |

</details>
</td>
</tr>

<tr>
<td><strong>Comparison Operators</strong></td>
<td>Compare field values</td>
<td>
<details><summary>Show</summary>

| Operator | Description | Example |
|---|---|---|
| `$eq` | Equal to | `{ age: { $eq: 25 } }` |
| `$ne` | Not equal to | `{ age: { $ne: 25 } }` |
| `$gt` | Greater than | `{ age: { $gt: 18 } }` |
| `$gte` | Greater than or equal | `{ age: { $gte: 18 } }` |
| `$lt` | Less than | `{ age: { $lt: 65 } }` |
| `$lte` | Less than or equal | `{ age: { $lte: 65 } }` |
| `$in` | Matches any value in array | `{ status: { $in: ["A","B"] } }` |
| `$nin` | Matches none in array | `{ status: { $nin: ["A","B"] } }` |

</details>
</td>
</tr>

</tbody>
</table>


<details>
<summary>Tools & Interfaces</summary>

- **MongoDB Compass** — GUI for browsing and managing data
- **Mongosh** — MongoDB Shell (interactive CLI)
- **MongoDB for VS Code** — Extension for querying from the editor

</details>

---

<details>
<summary>Indexes</summary>

```mermaid
graph TD
    A[Query] --> B{Index exists?}
    B -- Yes --> C[Index Scan - fast]
    B -- No --> D[Collection Scan - slow]
    C --> E[Return Documents]
    D --> E
```

</details>

---

<details>
<summary>Index Types & Commands</summary>

| Type | Description | Command |
|---|---|---|
| Single Field | Index on one field | `db.col.createIndex({ field: 1 })` |
| Compound | Index on multiple fields | `db.col.createIndex({ a: 1, b: -1 })` |
| Multikey | Index on array fields | Auto-created when field is array |
| Text | Full-text search | `db.col.createIndex({ field: "text" })` |
| TTL | Auto-delete docs after expiry | `db.col.createIndex({ date: 1 }, { expireAfterSeconds: 3600 })` |

**Tips:**
- `1` = ascending, `-1` = descending
- Use `db.col.getIndexes()` to list indexes
- Use `explain("executionStats")` to verify index usage

</details>

---

## References

- [Fireship - MongoDB in 100 Seconds](https://www.youtube.com/watch?v=-bt_y4Loofg)
- [MongoDB Explained in 10 Minutes](https://www.youtube.com/watch?v=GV9VBwH_h1U)
- [Bro Code - Learn MongoDB in 1 hour](https://www.youtube.com/watch?v=c2M-rlkkT5o)