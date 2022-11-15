<template>
  <main>
    <div :style="{ background: 'var(--color-fill-2)', padding: '28px' }" >
    <a-layout-content>
    <a-typography-title :heading="6">
             Network Topology

             <div id="mountNode">

             </div>
      </a-typography-title>
    </a-layout-content>
    </div>
  </main>
</template>

<script>
import G6 from '@antv/g6';
import axios from 'axios';
export default {
  async mounted() {
    const response = await axios.get("topology");
    this.graph = response.data;
    const graph = new G6.Graph({
      container: 'mountNode', // String | HTMLElement，必须，在 Step 1 中创建的容器 id 或容器本身
      width: 1200, // Number，必须，图的宽度
      height: 800, // Number，必须，图的高度
    });
    graph.data(this.graph); // 读取 Step 2 中的数据源到图上
    graph.render(); 
  },
  data: function () {
    return {
      graph : {
        // 点集
          nodes: [
            {
              id: 'core-0',
              label: 'core-0',
              size: 80, 
            },
            {
              id: 'core-1', 
              label: 'core-1',
              size: 80,
            },
            {
              id: 'core-2', 
              label: 'core-2',
              size: 80,
            },
            {
              id: 'core-3', 
              label: 'core-3',
              size: 80,
            },
          ],
        edges: [
         
        ],
      }
    }
  }
}
</script>