<!-- App.vue -->
<template>
  <div id="app" class="app-root">
    <!-- Navbar (Optional) -->
    <b-navbar type="dark" variant="primary" class="py-3 justify-content-center">
      <b-navbar-brand href="#" class="w-100 text-center">
        <div>
          <span class="display-6 d-block" style="color: #90ff9f;">GREENPORT</span>
          <br />
          <span class="text-light small d-block">
            GREENPORT is a decision support tool to optimize port fuel storage capacities and fuel investment strategies for a sustainable future.
          </span>
        </div>
      </b-navbar-brand>
    </b-navbar>

    <!-- Main Content -->
    <main class="app-content">
      <div class="container mt-4">
        <div class="mx-3">
          <MainDashboard />
        </div>
      </div>
    </main>

    <!-- Footer -->
    <AppFooter />
  </div>
</template>

<script>
import MainDashboard from "./components/MainDashboard.vue";
import AppFooter from "./components/AppFooter.vue";

export default {
  name: "App",
  components: {
    MainDashboard,
    AppFooter,
  },
};
</script>

<style>
/* Base styling */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c502c;
  margin-top: 0;
}

/* Sticky footer layout */
.app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-content {
  flex: 1 0 auto; /* takes remaining height, pushes footer down */
}
</style>
