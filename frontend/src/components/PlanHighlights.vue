<template>
  <section class="plan-highlights">
    <button
      class="plan-highlights__toggle"
      type="button"
      :aria-expanded="isExpanded"
      @click="isExpanded = !isExpanded"
    >
      <span>Plan highlights</span>
      <i
        class="bi bi-chevron-right plan-highlights__arrow"
        :class="{ 'plan-highlights__arrow--expanded': isExpanded }"
        aria-hidden="true"
      ></i>
    </button>

    <div v-show="isExpanded" class="plan-highlights__content">
      <ul v-if="highlights.length" class="plan-highlights__list">
        <li v-for="highlight in highlights" :key="highlight">
          {{ highlight }}
        </li>
      </ul>
      <p v-else class="plan-highlights__empty">
        No tank schedule highlights are available.
      </p>
    </div>
  </section>
</template>

<script>
import { defineComponent } from 'vue';
import { buildPlanHighlights } from '@/utils/planHighlights.js';

export default defineComponent({
  name: 'PlanHighlights',
  props: {
    schedule: {
      type: Object,
      default: () => ({}),
    },
    years: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return { isExpanded: false };
  },
  computed: {
    highlights() {
      return buildPlanHighlights(this.schedule, this.years);
    },
  },
});
</script>

<style scoped>
.plan-highlights {
  margin-top: 1rem;
  width: 100%;
  text-align: left;
}

.plan-highlights__toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0;
  border: 0;
  background: transparent;
  color: #212529;
  font-size: 1rem;
  text-decoration: underline;
  cursor: pointer;
  text-align: left;
}

.plan-highlights__toggle:hover,
.plan-highlights__toggle:focus-visible {
  color: #0d6efd;
}

.plan-highlights__toggle:focus-visible {
  outline: 2px solid #0d6efd;
  outline-offset: 2px;
}

.plan-highlights__arrow {
  flex: 0 0 auto;
  transition: transform 0.2s ease;
}

.plan-highlights__arrow--expanded {
  transform: rotate(90deg);
}

.plan-highlights__content {
  width: 100%;
  max-width: 700px;
  text-align: left;
}

.plan-highlights__list {
  margin: 0;
  padding: 0.75rem 0 0 1.25rem;
  text-align: left;
}

.plan-highlights__list li {
  text-align: left;
}

.plan-highlights__list li + li {
  margin-top: 0.5rem;
}

.plan-highlights__empty {
  margin: 0;
  padding-top: 0.75rem;
  color: #6c757d;
  text-align: left;
}
</style>
