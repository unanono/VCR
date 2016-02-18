# -*- coding: utf-8 *-*

import tornado.web


#Esto se podria usar para inyectar javascript para el replay
#se debe incluir {{ modules.Index }} que se define en los
#settings de la App en los templates o donde se quiera inyectar el js
class IndexModule(tornado.web.UIModule):
    def embedded_javascript(self):
        return 'alert("Hola desde tornado")'

    def render(self):
        return self.render_string("templates/pp.html")
