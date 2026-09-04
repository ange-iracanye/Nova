// Production bootstrap order matters: install the API route compatibility layer before
// the React application captures window.fetch for credentials and API calls.
import "./production-api.js";
import "./main.jsx";
