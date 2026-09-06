# -*- coding: utf-8 -*-
from urllib import quote
from models import Project as ProjectModel
from utils import render
from default.tracker.layout import Layout


def _id(value):
    value = str(value or "")
    if not value.isdigit() or len(value) > 10:
        return None
    result = int(value)
    return result if 0 < result <= 2147483647 else None


def _fail(ctx, status, message):
    ctx.page_layout = False
    ctx.go_to = render.as_string(ctx, message)


def _project(ctx, value):
    identity = _id(value)
    row = (ProjectModel.first("id = ? AND owner_id = ?", identity,
                              ctx.output["current_user"]["id"])
           if identity else None)
    if row is None:
        _fail(ctx, 404, "Project not found")
    return row


def _page(ctx):
    return min(_id(ctx.getParameter("page")) or 1, 10000)


class Project(Layout):
    ACCESS_POLICY = {
        "view": "permission:projects.read",
        "edit": "permission:projects.write",
        "save": "permission:projects.write",
        "delete": "permission:projects.delete",
    }

    def view(self, ctx):
        query = unicode(ctx.getParameter("q") or "").strip()[:120]
        page = _page(ctx)
        rows = list(ProjectModel.where(
            "owner_id = ? AND name LIKE ?", ctx.output["current_user"]["id"],
            "%" + query + "%").orderBy("id DESC").limit(21).offset((page - 1) * 20))
        base = ctx.ctxPath + "/t/tracker/project?q=" + quote(query.encode("utf-8"))
        ctx.output["projects"] = rows[:20]
        ctx.output["q"] = query
        ctx.output["page"] = page
        ctx.output["previous_url"] = base + "&page=%d" % (page - 1) if page > 1 else None
        ctx.output["next_url"] = base + "&page=%d" % (page + 1) if len(rows) > 20 else None
        ctx.go_to = render.as_view(ctx, "project")

    def edit(self, ctx):
        identity = ctx.getParameter("id")
        row = _project(ctx, identity) if identity else None
        if identity and row is None:
            return
        ctx.output["project"] = row
        ctx.go_to = render.as_view(ctx, "edit")

    def save(self, ctx):
        """POST"""
        identity = ctx.getParameter("id")
        row = _project(ctx, identity) if identity else None
        if identity and row is None:
            return
        name = unicode(ctx.getParameter("name") or "").strip()
        if not name or len(name) > 120:
            ctx.output["project"] = {"id": identity, "name": name}
            ctx.output["error"] = "Enter a project name of 1 to 120 characters."
            ctx.go_to = render.as_view(ctx, "edit")
            return
        if row is None:
            row = ProjectModel()
            row.set("owner_id", ctx.output["current_user"]["id"])
        row.set("name", name)
        row.saveIt()
        ctx.go_to = ctx.ctxPath + "/t/tracker/project"

    def delete(self, ctx):
        """POST"""
        row = _project(ctx, ctx.getParameter("id"))
        if row is None:
            return
        row.delete()
        ctx.go_to = ctx.ctxPath + "/t/tracker/project"
