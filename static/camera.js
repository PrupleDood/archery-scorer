let filename;

// Function to open the camera
function openCamera() {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            // Access the camera stream
            const video = document.createElement('video');
            video.srcObject = stream;
            video.autoplay = true;
            document.body.appendChild(video);
        })
        .catch(error => {
            console.error('Error accessing camera:', error);
        });
}

// Function to choose an image
function chooseImage() {
    const input = document.querySelector('input[type="file"]');
    const selectedImage = document.getElementById('selectedImage');

    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function (e) {
            // Display the selected image
            selectedImage.src = e.target.result;
            selectedImage.style.display = 'block';

            // Upload image to backend
            uploadImage(input.files[0]);
        };

        filename = input.files[0].name;

        reader.readAsDataURL(input.files[0]);
    }
}

// Function to upload the image
function uploadImage(selectedImageData) {
    if (selectedImageData) {
        const formData = new FormData();
        formData.append('image', selectedImageData);

        fetch('/images', {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            console.log('Image uploaded successfully:', data);
            // Handle the server response as needed
        })
        .catch(error => {
            console.error('Error uploading image:', error);
        });
    } else {
        console.warn('No image selected.');
    }
}


async function processImage() {
    const formData = new FormData();
    formData.append('filename', filename);

    let scores;

    await fetch('/process_image', {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        scores = data["scores"];
        console.log('Image processed succesfully', data);
    })
    .catch(error => {
        console.log("Error processing image", error);
    });

    let rows = document.getElementById("score_table").children[0].children
    // let fiften_rows = document.getElementById("15m").children[0].children

    // scores.forEach(element => {
    //     element.join("  ")
    // });

    let sc_i = 0;

    for (let i = 1; i < rows.length; i++) {
        if (i == 4) { continue; }

        rows[i].innerHTML = scores[sc_i];

        sc_i++;

    }

}
