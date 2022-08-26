const path = require('path');

module.exports = {
  entry: { sga:'./assets/sgaeditor.js'
           },  // path to our input file
  output: {
    filename: '[name]-bundle.js',  // output bundle file name
    path: path.resolve(__dirname, './src/sga/static/sga/'),  // path to our Django static directory
  },

  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        loader: "babel-loader",
        options: { presets: ["@babel/preset-env", "@babel/preset-react"] }
      },
    ]
  }
};