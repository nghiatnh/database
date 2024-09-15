### STATEMENTS

**statements**: (*statement* `;`)*
**statement**: *create_table* | *drop_table* | *select* | *insert* | *update* | *delete*

### TABLE

**create_table**: `CREATE` `TABLE` *table_name* `(` *declarations* `)`
**drop_table**: `DROP` `TABLE` *table_name*
**declarations**: *field_decls* (`,` *index_decls*)? `,` *primary_key_decl*
**field_decls**: *field_decl* (`,` *field_decl*)*
**field_decl**: *field_name* *type*
**index_decls**: *index_decl* (`,` *index_decl*)*
**index_decl**: `INDEX` *tuple_decl*
**primary_key_decl**: `PRIMARY` `KEY` *tuple_decl*
**tuple_decl**: `(` *field_name* (`,` *field_name*)* `)`
**table_name**: **ID**
**field_name**: **ID**
**type**: `INTEGER` | `STRING`

### SELECT

**select**: `SELECT` *select_expr* `FROM` *table_name* *conditions* *limit*?
**select_expr**: *as_expr* (`,` *as_expr*)* | `(` *select_expr* `)`
**as_expr**: *field_name* (`AS` *field_name*)?
**conditions**: *index*? *filter*?
**limit**: `LIMIT` *number*
**index**: `INDEX` `BY` *condition* (`AND` *condition*)?
**filter**: `FILTER` *condition* (`AND` | `OR` | `NOT` *condition*)*
**condition**: *field_name* *compare* *expr*


### INSERT/ UPDATE/ DELETE

**insert**: `INSERT` `INTO` *table_name* *tuple_decl* `VALUES` *tuple_values*
**update**: `UPDATE` *table_name* `SET` *set_expr* (`,` *set_expr*)* *conditions* *limit*
**delete**: `DELETE` `FROM` *table_name* *conditions* *limit*
**tuple_values**: `(` *value* (`,` *value*)* `)`
**set_expr**: *field_name* `=` *expr*

### EXPRESSION

**value**: *number* | *string*
**number**: [1-9][0-9]*
**string**: `'` *any** `'`
**expr**: *logic* (*compare* *logic*)*
**logic**: *term* ((`+` | `-`) *term*)*
**term**: *factor* ((`*` | `\` | `%`) *factor*)*
**factor**: *unary* | *value* | `(` *expr* `)`
**unary**: (`+` | `-`) *factor*
**compare**: `=` | `!=` | `>` | `<` | `>=` | `<=`
