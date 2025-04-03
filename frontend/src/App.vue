<!-- App.vue -->
<template>
  <div id="app">
    <!-- Navbar (Optional) -->
    <b-navbar type="dark" variant="primary" class="py-3 justify-content-center">
      <b-navbar-brand href="#" class="w-100 text-center">
        <div>
            <span class="display-6 d-block" style="color: #90ff9f;">GREENPORT</span>
          <br />
          <span class="text-light small d-block">GREENPORT is your decision support tool to optimize port fuel capacities and fuel investment strategies for a sustainable future.</span>
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
  color: #2c502c;
  margin-top: 0;
}
</style>
