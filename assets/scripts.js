function clickThemeIcon (themeIcon) {
  var themeImage = document.getElementById("image-theme");
  if (themeIcon.value == 1) {
    themeImage.src = "media/wike-dark.png";
  } else {
    themeImage.src = "media/wike-light.png";
  }
}

function clickFeaturesIcon (featuresIcon) {
  var featuresImage = document.getElementById("image-features");
  var featuresTitle = document.getElementById("title-features");
  var featuresText = document.getElementById("text-features");
  if (featuresIcon.value == 1) {
    featuresImage.src = "media/wike-bookmarks.png";
    featuresTitle.textContent = "Bookmarks";
    featuresText.textContent = "Save the articles you want to keep to read later.";
  } else if (featuresIcon.value == 2) {
    featuresImage.src = "media/wike-historic.png";
    featuresTitle.textContent = "Recent Articles";
    featuresText.textContent = "Use the history to access the last visited articles.";
  } else {
    featuresImage.src = "media/wike-toc.png";
    featuresTitle.textContent = "Table of Contents";
    featuresText.textContent = "Quickly scroll through the various sections of the article.";
  }
}

