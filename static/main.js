function hasClass(element, className) {
    return element.className && new RegExp("(^|\\s)" + className + "(\\s|$)").test(element.className);
}

function replaceClass(element, oldClassName, newClassName) {
    console.log(element.className)
    element.className = element.className.replace(oldClassName, newClassName);
}

window.onload = function () {
    var subjects = document.getElementsByClassName('subject');
    for (var i = 0; i < subjects.length; i++) {
        console.log(subjects[i])
        subjects[i].addEventListener('click', function () {
            console.log('click')
            if (hasClass(this.parentNode, "selected")) {
                replaceClass(this.parentNode, "selected", "unselected");
            } else {
                replaceClass(this.parentNode, "unselected", "selected");
            }
        })
    }
};
