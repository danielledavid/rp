from flask import Flask, request, render_template, Response
import sqlite3
import csv

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('rp.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    fireplace_types = conn.execute('SELECT * FROM fireplace_type').fetchall()

    owners = []
    filter_applied = False

    if request.method == 'POST':
        selected_type = request.form.get('fireplace_type')
        if selected_type:
            query = """
                SELECT * FROM owner
                WHERE muni_parcel IN (
                    SELECT muni_parcel FROM res_bldg
                    WHERE fireplace_type IN (
                        SELECT code FROM fireplace_type WHERE description = ?
                    )
                )
            """
            owners = conn.execute(query, (selected_type,)).fetchall()
            filter_applied = True

    conn.close()
    return render_template('index.html', owners=owners, fireplace_types=fireplace_types, filter_applied=filter_applied)

@app.route('/export', methods=['GET'])
def export():
    conn = get_db_connection()
    query = """
        SELECT * FROM owner
        WHERE muni_parcel IN (
            SELECT muni_parcel FROM res_bldg
            WHERE fireplace_type IN (
                SELECT code FROM fireplace_type WHERE description = ?
            )
        )
    """
    selected_type = request.args.get('fireplace_type')
    if not selected_type:
        return "No filter applied", 400

    owners = conn.execute(query, (selected_type,)).fetchall()
    conn.close()

    def generate():
        data = [dict(row) for row in owners]
        output = csv.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        yield output.getvalue()

    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=owners.csv"})

if __name__ == '__main__':
    app.run(debug=True)
