from flask import Flask, render_template


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def dashboard():
        return render_template("dashboard.html")

    @app.get("/simulaciones/<simulation_id>")
    def detalle(simulation_id):
        return render_template("detalle.html", simulation_id=simulation_id)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
