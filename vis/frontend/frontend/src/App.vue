<template>
  <div class="menu-demo" :style="{ background: 'var(--color-fill-2)' }">
    <a-layout style="height: 1000px">
      <a-layout-header>
        <a-menu mode="horizontal" :default-selected-keys="['1']">
          <a-menu-item
            key="0"
            :style="{ padding: 0, marginRight: '38px' }"
            disabled
          >
            <a-typography-title :heading="6">
              Data Center Network Emluator
            </a-typography-title>
          </a-menu-item>
          <router-link to="/">
            <a-menu-item key="1">
            Home
            </a-menu-item>
          </router-link>
          <router-link to="/about">
          <a-menu-item key="2">
           about
          </a-menu-item>
        </router-link>
        </a-menu>
      </a-layout-header>

      <a-layout-content>
        <router-view>

        </router-view>
      </a-layout-content>
      <a-layout-footer></a-layout-footer>
    </a-layout>
  </div>
 
</template>

<style>
body {
  font-family: Arial, Helvetica, sans-serif;
}
</style>
