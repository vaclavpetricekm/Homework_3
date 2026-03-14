import io
from PIL import Image


def visualize(graph, output_file_name):
    try:
        png = graph.get_graph().draw_mermaid_png()
   
        pil_image = Image.open(io.BytesIO(png)) 

      
        output_file = output_file_name 
        pil_image.save(output_file, 'PNG')
    except Exception:
        pass
    
