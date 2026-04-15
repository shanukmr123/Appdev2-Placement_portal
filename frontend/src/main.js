import { createApp } from "vue";
import App from "../components/DashboardComponent.vue";

// Optional: import global CSS
import "../static/shaanu-theme.css";

// Create app
const app = createApp(App);

// Mount
app.mount("#app");