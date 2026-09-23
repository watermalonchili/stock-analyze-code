import {createRouter, createWebHashHistory} from 'vue-router'
import Main from '../views/Main copy1.vue'

const routes = [
    {
        path: '/',
        name: 'main',
        component: Main,
        children: [
            {
                path: '/modeCards',
                name: 'modeCards',
                component: () => import('../views/ModeCards.vue')
            },
            {
                path:'/resultShow',
                name: 'resultShow',
                component: () => import('../views/ResultShow.vue')
            },
            {
                path: '/graph',
                name: 'graph',
                component: () => import('../views/Graph.vue')
            }
        ]
    }
]

const router = createRouter({
    history: createWebHashHistory(),
    routes
})

export default router