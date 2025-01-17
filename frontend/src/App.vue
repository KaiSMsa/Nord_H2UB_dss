<!-- App.vue -->
<template>
  <div id="app">
    <!-- Navbar (Optional) -->
    <b-navbar type="dark" variant="primary" class="py-3 justify-content-center">
      <b-navbar-brand href="#" class="w-100 text-center">
        <div>
          <span class="display-6 d-block">Green Fuel Planner</span>
          <br />
          <span class="text-muted small d-block">A decision support tool for planning and optimizing fuel investments for Ports</span>
        </div>
      </b-navbar-brand>
    </b-navbar>

    <!-- Main Content -->
    <div class="container mt-4">
      <div class="mx-3">
        <MainDashboard />
      </div>
    </div>
  </div>
</template>

<script>
// Import the Dashboard component
import MainDashboard from './components/MainDashboard.vue';

export default {
  name: 'App',
  components: {
    MainDashboard
  }
};
</script>
<style>
/* Optional: Additional styling to ensure layout consistency */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 0;
}
</style>

<!-- <style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 20px;
}
.main-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh; /* Full viewport height */
}

</style> -->