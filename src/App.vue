<!-- App.vue -->
<template>
  <!-- <div id="app"> -->
    <!-- Navbar (Optional) -->
    <!-- <b-navbar type="dark" variant="primary">
      <b-navbar-brand href="#">Decision Support Tool</b-navbar-brand>
    </b-navbar> -->

    <!-- Main Dashboard Component -->
    <MainDashboard />
    <!-- <ResultBarChart /> -->
  <!-- </div> -->
</template>

<script>
// Import the Dashboard component
import MainDashboard from './components/MainDashboard.vue';
// import ResultBarChart from './components/ResultBarChart.vue';

export default {
  name: 'App',
  components: {
    MainDashboard
  //  ResultBarChart
  }
};
</script>

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