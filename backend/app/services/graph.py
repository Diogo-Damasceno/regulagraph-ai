from neo4j import GraphDatabase
from app.config import get_settings


def upsert_norm(norm, relations: list[dict]) -> None:
    settings = get_settings()
    try:
        with GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)) as driver:
            driver.execute_query(
                "MERGE (n:Norm {id: $id}) SET n.title=$title, n.agency=$agency",
                id=norm.id, title=norm.title, agency=norm.agency,
            )
            for relation in relations:
                driver.execute_query(
                    "MATCH (n:Norm {id:$id}) MERGE (t:Reference {name:$target}) "
                    "MERGE (n)-[:RELATES_TO {kind:$kind}]->(t)",
                    id=norm.id, target=relation["target"], kind=relation["type"],
                )
    except Exception:
        # Graph persistence must not invalidate the canonical relational transaction.
        return
