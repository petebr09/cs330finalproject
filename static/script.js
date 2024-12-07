let currentAnimalIndex = 0;

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
    console.log(`Liked: ${animals[currentAnimalIndex].name}`);
    currentAnimalIndex++;
    showAnimal();
}

function dislikeAnimal() {
    console.log(`Disliked: ${animals[currentAnimalIndex].name}`);
    currentAnimalIndex++;
    showAnimal();
}

document.addEventListener("DOMContentLoaded", showAnimal);
