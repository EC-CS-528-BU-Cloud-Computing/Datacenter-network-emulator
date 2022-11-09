<template>
  <main>
    <div :style="{ background: 'var(--color-fill-2)', padding: '28px' }" >
    <a-layout-content>
    <a-typography-title :heading="5">
             About Us
    </a-typography-title>
    <a-typography-paragraph>
     Team Members:  Mingji Han, Ayesha Naeem, Alex Hureaux-Perron, Muhammad Fahad Farid, Zeying Zhu
    </a-typography-paragraph>
  </a-layout-content>
  </div>
  </main>
</template>

<style>
@media (min-width: 1024px) {
  .about {
    min-height: 100vh;
    display: flex;
    align-items: center;
  }
}
</style>
