# React GitHub Pages

# Steps
```
// In React Project directory
npm install gh-pages --save-dev

//Update package.json
+   "homepage": "https://crossproducts.github.io/Notes/React/Projects/Todo-List",

// Update package.json
"scripts": {
+   "predeploy": "npm run build",
+   "deploy": "gh-pages -d build",
...
}

// Update package.json
"deploy": "gh-pages -d build" --> "deploy": "gh-pages -d dist"

// Deploy Project
npm run deploy
```


# References
[Youtube: Code Commerce - Publish A React App to GitHub Pages - Less Than 3 minites](https://www.youtube.com/watch?v=4G6O0BIoq6M)
[GitHub: react-gh-pages](https://github.com/gitname/react-gh-pages)