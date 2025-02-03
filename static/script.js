// Webcam Setup
const video = document.getElementById('webcam');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let webcamStream;

document.getElementById('start-webcam').addEventListener('click', async () => {
    if (!webcamStream) {
        webcamStream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = webcamStream;
        video.play();
        setInterval(detectWebcamFrame, 100); // Detect every 100ms
    }
});

async function detectWebcamFrame() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const image_data_url = canvas.toDataURL('image/jpeg');

    fetch('/detect_webcam', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: image_data_url }),
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('webcam-text').innerText = `Detected Text: ${data.text}`;

        // Clear canvas before drawing
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        console.log("Received boxes:", data.boxes); // Debugging output

        // Draw bounding boxes if they exist
        if (data.boxes && data.boxes.length > 0) {
            ctx.strokeStyle = "green";
            ctx.lineWidth = 2;
            ctx.font = "16px Arial";
            ctx.fillStyle = "green";

            data.boxes.forEach(box => {
                ctx.strokeRect(box.x1, box.y1, box.x2 - box.x1, box.y2 - box.y1);
                ctx.fillText(box.label, box.x1, box.y1 - 5);
            });
        }
    })
    .catch(error => console.error("Error detecting objects:", error));
}


// Image Upload
document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData();
    const fileInput = document.getElementById('image-upload');
    formData.append('file', fileInput.files[0]);

    const response = await fetch('/detect_image', {
        method: 'POST',
        body: formData,
    });

    const data = await response.json();
    document.getElementById('result-image').src = data.image;
    document.getElementById('result-image').style.display = 'block';
    document.getElementById('upload-text').innerText = `Detected Text: ${data.text}`;
});
document.getElementById('text-to-sign-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const inputText = document.getElementById('input-text').value.trim();

    if (!inputText) {
        alert("Please enter some text to translate.");
        return;
    }

    // Clear previous results
    const signImagesContainer = document.getElementById('sign-images-container');
    signImagesContainer.innerHTML = '';
    const noResultsMessage = document.getElementById('no-results-message');
    noResultsMessage.style.display = 'none';

    // Send the input text to the backend
    const response = await fetch('/translate_text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText }),
    });

    const data = await response.json();

    if (data.error) {
        alert(data.error); // Display error message from the backend
        return;
    }

    if (data.images.length === 0) {
        // Show a message if no images are available
        noResultsMessage.style.display = 'block';
        return;
    }

    // Display the translated sign language images
    data.images.forEach(imageUrl => {
        const img = document.createElement('img');
        img.src = imageUrl; // Use the URL directly
        img.alt = "Sign Language Image";
        img.classList.add('sign-image'); // Optional: Add a class for styling
        signImagesContainer.appendChild(img);
    });
});