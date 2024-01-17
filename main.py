from CardScorer import ScoreCard as ScCard
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("static_demo.html")


@app.route("/images", methods = ["POST"])
def upload_image():
    try:
        # Get the uploaded image from the request
        uploaded_image = request.files['image']

        # Save the image to a desired location or process it as needed
        # For example, save to the 'uploads' folder

        uploaded_image.save('images/' + uploaded_image.filename)

        # Perform any additional processing if required
        # ...

        return jsonify({'message': 'Image uploaded successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/process_image", methods = ["POST"])
def process_image():
    try:
        filename = request.form.get("filename")

        card = ScCard(
            filename = f"images/{filename}",
            score_type = ScCard.MUTLIPLE
        )

        scores = [str(score_round.tolist())[1:-1] for score_round in card.scores]  

        return jsonify({'scores': scores})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug = True)


