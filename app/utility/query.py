from app.utility.model import BaseFilter


def build_query(filter: BaseFilter) -> dict:
    q = {}

    if filter.status:
        q["status"] = filter.status

    if filter.search:
        q["name"] = {"$regex": filter.search, "$options": "i"}

    if filter.created_from or filter.created_to:
        q["created_at"] = {}
        if filter.created_from:
            q["created_at"]["$gte"] = filter.created_from
        if filter.created_to:
            q["created_at"]["$lte"] = filter.created_to

    return q