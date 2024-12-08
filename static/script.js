let currentAnimalIndex = 0;
let animalList = [];

async function fetchAnimals() {
    try {
        const response = await fetch('/api/animals');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        animalList = await response.json();
        showAnimal();
    } catch (error) {
        console.error("Error fetching animals:", error);
        const animalContainer = document.getElementById('animal-container');
        animalContainer.innerHTML = `
            <div class="text-center mt-5">
                <h3>Unable to load animals</h3>
                <p>Please try again later.</p>
            </div>
        `;
    }
}

function showAnimal() {
    const animalContainer = document.getElementById('animal-container');
    if (currentAnimalIndex < animalList.length) {
        const animal = animalList[currentAnimalIndex];
        animalContainer.innerHTML = `
            <div class="animal-card">
                <h2>${animal.name}</h2>
                <img src="${animal.image || '/static/default-animal.jpg'}" alt="${animal.name}">
                <p>Species: ${animal.species}</p>
                <p>Breed: ${animal.breed || 'Unknown'}</p>
                <p>Age: ${animal.age} years</p>
                <p>${animal.description}</p>
                <div class="action-buttons">
                    <button class="btn btn-success" onclick="likeAnimal()">Like</button>
                    <button class="btn btn-danger" onclick="dislikeAnimal()">Dislike</button>
                </div>
            </div>
        `;
    } else {
        animalContainer.innerHTML = `
            <div class="text-center mt-5">
                <h3>No more animals to display!</h3>
                <p>Check back later for more furry friends.</p>
            </div>
        `;
    }
}

function likeAnimal() {
    console.log(`Liked: ${animalList[currentAnimalIndex].name}`);
    currentAnimalIndex++;
    showAnimal();
}

function dislikeAnimal() {
    console.log(`Disliked: ${animalList[currentAnimalIndex].name}`);
    currentAnimalIndex++;
    showAnimal();
}

document.addEventListener("DOMContentLoaded", fetchAnimals);