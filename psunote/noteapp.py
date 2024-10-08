import flask

import models
import forms


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/delete/<int:note_id>")
def notes_delete(note_id):
    print("Note deleted")
    db = models.db
    note = (
        db.session.execute(db.select(models.Note).where(models.Note.id == note_id))
        .scalars()
        .first()
    )

    if note:
        db.session.delete(note)
        db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)

    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        print("tag_name", tag_name)
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/notes/update/<int:note_id>", methods=["GET", "POST"])
def notes_update(note_id):
    db = models.db
    note = (
        db.session.execute(db.select(models.Note).where(models.Note.id == note_id))
        .scalars()
        .first()
    )

    form = forms.NoteForm(obj=note)

    if flask.request.method == "GET":
        form.tags.data = [tag.name for tag in note.tags]

    if form.validate_on_submit():
        note.title = form.title.data
        note.description = form.description.data
        note.tags.clear()
        for tag_name in form.tags.data:
            tag = (
                db.session.execute(
                    db.select(models.Tag).where(models.Tag.name == tag_name)
                )
                .scalars()
                .first()
            )
            if not tag:
                tag = models.Tag(name=tag_name)
                db.session.add(tag)

            note.tags.append(tag)
        db.session.commit()
        return flask.redirect(flask.url_for("index"))

    return flask.render_template(
        "notes-update.html",
        form=form,
        note=note,
    )


@app.route("/tags/<tag_name>", methods=["GET", "POST"])
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    if flask.request.method == "POST":
        print("TEST")
        db = models.db
        if tag:
            for note in notes:
                if tag in note.tags:
                    note.tags.remove(tag)
            db.session.commit()
            db.session.delete(tag)
            db.session.commit()
        return flask.redirect(flask.url_for("index"))

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )


if __name__ == "__main__":
    app.run(debug=True)
