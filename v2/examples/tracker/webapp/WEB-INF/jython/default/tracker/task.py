# -*- coding: utf-8 -*-
import re
from java.sql import Blob
from models import Task as TaskModel, Attachment, Soad_auth_user
from default.tracker.project import _id, _fail, _project, _page
from default.tracker.layout import Layout
from utils import render


def _task(ctx, project, identity):
    row = TaskModel.first("id = ? AND project_id = ?", _id(identity) or -1,
                          project.getId())
    if row is None:
        _fail(ctx, 404, "Task not found")
    return row


def _form(ctx, project, task, error=None):
    ctx.output["project"] = project
    ctx.output["task"] = task
    # Never pass entire authentication models (including password fields) to a view.
    ctx.output["people"] = [
        {"id": user.getId(), "full_name": user.get("full_name")}
        for user in Soad_auth_user.where("status = ?", "active").orderBy("full_name ASC")]
    ctx.output["error"] = error
    ctx.go_to = render.as_view(ctx, "edit")


class Task(Layout):
    ACCESS_POLICY = {
        "view": "permission:tasks.read",
        "data": "permission:tasks.read",
        "download": "permission:tasks.read",
        "edit": "permission:tasks.write",
        "save": "permission:tasks.write",
        "delete": "permission:tasks.write",
    }

    def _rows(self, ctx, project):
        status = str(ctx.getParameter("status") or "")
        if status and status not in ("todo", "doing", "done"):
            _fail(ctx, 400, "Invalid task status")
            return None
        page = _page(ctx)
        query = TaskModel.where("project_id = ?", project.getId())
        if status:
            query = TaskModel.where("project_id = ? AND status = ?", project.getId(), status)
        rows = list(query.orderBy("id DESC").limit(21).offset((page - 1) * 20))
        base = "%s/t/tracker/task?project_id=%s&status=%s" % (
            ctx.ctxPath, project.getId(), status)
        ctx.output["status"] = status
        ctx.output["page"] = page
        ctx.output["previous_url"] = base + "&page=%d" % (page - 1) if page > 1 else None
        ctx.output["next_url"] = base + "&page=%d" % (page + 1) if len(rows) > 20 else None
        return rows[:20]

    def view(self, ctx):
        project = _project(ctx, ctx.getParameter("project_id"))
        if project is None:
            return
        rows = self._rows(ctx, project)
        if rows is None:
            return
        ctx.output["project"] = project
        ctx.output["tasks"] = rows
        ctx.go_to = render.as_view(ctx, "task")

    def data(self, ctx):
        project = _project(ctx, ctx.getParameter("project_id"))
        if project is None:
            return
        rows = self._rows(ctx, project)
        if rows is None:
            return
        ctx.page_layout = False
        ctx.go_to = render.as_json(ctx, {"tasks": [
            {"id": row.getId(), "title": row.get("title"), "status": row.get("status")}
            for row in rows], "page": ctx.output["page"],
            "has_next": bool(ctx.output.get("next_url"))})

    def edit(self, ctx):
        project = _project(ctx, ctx.getParameter("project_id"))
        if project is None:
            return
        identity = ctx.getParameter("id")
        row = _task(ctx, project, identity) if identity else None
        if identity and row is None:
            return
        _form(ctx, project, row)

    def save(self, ctx):
        """POST"""
        project = _project(ctx, ctx.getParameter("project_id"))
        if project is None:
            return
        identity = ctx.getParameter("id")
        row = _task(ctx, project, identity) if identity else None
        if identity and row is None:
            return
        title = unicode(ctx.getParameter("title") or "").strip()
        status = str(ctx.getParameter("status") or "")
        assignee = str(ctx.getParameter("assignee_id") or "").strip()
        draft = {"id": identity, "title": title, "status": status, "assignee_id": assignee}
        error = None
        if not title or len(title) > 200:
            error = "Enter a task title of 1 to 200 characters."
        elif status not in ("todo", "doing", "done"):
            error = "Choose todo, doing, or done."
        elif assignee and Soad_auth_user.first("id = ? AND status = ?", assignee, "active") is None:
            error = "Choose an active application user."
        # WebContext.getParameter returns Java String; files require the wrapper.
        upload = ctx.getRequest().getParameter("attachment")
        if upload and (not hasattr(upload, "getBytes") or upload.getSize() > 1048576):
            error = "Choose a file no larger than 1 MiB."
        if error:
            _form(ctx, project, draft, error)
            return
        if row is None:
            row = TaskModel()
            row.set("project_id", project.getId())
        row.set("title", title)
        row.set("status", status)
        row.set("assignee_id", assignee or None)
        row.saveIt()
        existing = Attachment.first("task_id = ?", row.getId())
        if ctx.getParameter("remove_attachment") == "yes" and existing is not None:
            existing.delete()
            existing = None
        if upload:
            attached = existing if existing is not None else Attachment()
            attached.set("task_id", row.getId())
            # ASCII, bounded, and safe for a quoted Content-Disposition filename.
            filename = re.sub(r"[^A-Za-z0-9._-]", "_", unicode(upload.getFileName()))[:120]
            attached.set("filename", filename if filename.strip(".") else "download.bin")
            attached.set("content", upload.getBytes())
            attached.saveIt()
        ctx.go_to = "%s/t/tracker/task?project_id=%s" % (ctx.ctxPath, project.getId())

    def download(self, ctx):
        project = _project(ctx, ctx.getParameter("project_id"))
        if project is None:
            return
        row = _task(ctx, project, ctx.getParameter("id"))
        if row is None:
            return
        attached = Attachment.first("task_id = ?", row.getId())
        if attached is None:
            _fail(ctx, 404, "No attachment")
            return
        ctx.page_layout = False
        ctx.getResponse().setHeader("X-Content-Type-Options", "nosniff")
        ctx.getResponse().setHeader("Cache-Control", "no-store")
        content = attached.get("content")
        if isinstance(content, Blob):
            content = content.getBytes(1, int(content.length()))
        ctx.go_to = render.as_blob(ctx, content,
                                  "application/octet-stream", attached.get("filename"),
                                  attachment=True)

    def delete(self, ctx):
        """POST"""
        project = _project(ctx, ctx.getParameter("project_id"))
        if project is None:
            return
        row = _task(ctx, project, ctx.getParameter("id"))
        if row is None:
            return
        row.delete()
        ctx.go_to = "%s/t/tracker/task?project_id=%s" % (ctx.ctxPath, project.getId())
