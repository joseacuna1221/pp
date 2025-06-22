let nextBtn = document.querySelector('.next')
let prevBtn = document.querySelector('.prev')

let slider = document.querySelector('.slider')
let sliderList = slider.querySelector('.slider .list')
let thumbnail = document.querySelector('.thumbnail')
let thumbnailItems = thumbnail.querySelectorAll('.item')

thumbnail.appendChild(thumbnailItems[0])

// Funcion para next button
nextBtn.onclick = function(){
    moveSlider('next')
}

// Funcion para prev button
prevBtn.onclick = function(){
    moveSlider('prev')
}

function moveSlider(direction){
    let sliderItems = slider.querySelectorAll('.item')
    if(direction === 'next'){
        sliderList.appendChild(sliderItems[0])
        thumbnail.appendChild(thumbnailItems[0])
        slider.classList.add('next')
    }
}