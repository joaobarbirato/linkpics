from xlwt import Workbook, easyxf
import os


def CriarArquivoXls(titulo_noticia,legenda_noticia,lst_entidades_fisicas,lst_entidades_objetos,lst_entidades_interseccao,lst_entidades_diferenca,lst_entidades_nomeadas,dicionario_wup_fisicas,dicionario_wup_objetos,dicionario_embeddings_fisicas,dicionario_embeddings_objetos,lst_objetos,file_chooseWup,file_chooseEmbedding,noticia_anotada,dicionario_dif_entidades_wup,dicionario_dif_entidades_embeddings):
    wb = Workbook()
    #Setando cores do estilo
    style_red= easyxf('pattern: pattern solid, fore_colour red;')
    style_silver= easyxf('pattern: pattern solid, fore_colour 0x16;')
    style_green= easyxf('pattern: pattern solid, fore_colour 0x3B;')
    style_pink= easyxf('pattern: pattern solid, fore_colour pink;')
    style_orange= easyxf('pattern: pattern solid, fore_colour orange;')
    style_yellow= easyxf('pattern: pattern solid, fore_colour yellow;')
    style_ice= easyxf('pattern: pattern solid, fore_colour 0x1F ;')
    style_lightOrange= easyxf('pattern: pattern solid, fore_colour 0x34 ;')
    style_ocean_blue= easyxf('pattern: pattern solid, fore_colour 0x1E ;')
    change_color_dif= False


    sheet_rotulos = wb.add_sheet('Regiões da imagem')
    #Escrevendo no sheet sheet_rotulos
    titulo_noticia= titulo_noticia
    legenda_noticia= legenda_noticia
    sheet_rotulos.col(2).width= 4500 #regula o tamanho da coluna em parenteses
    sheet_rotulos.write(0,0,'NOTÍCIA',style_ice) #escreve noticia no label
    sheet_rotulos.write(0,1,titulo_noticia) #escreve titulo da noticia
    sheet_rotulos.write(1,0,'LEGENDA',style_ice) #escreve legenda no label {coluna 1}
    sheet_rotulos.write(1,1,legenda_noticia) #escreve a legenda da noticia {coluna1}
    sheet_rotulos.write(2,0,'PALAVRAS anotadas em AZUL estão anotadas pela ferramenta.',style_red) #escreve a legenda da noticia {coluna1}
    #Informações do Rótulo
    inic= 4
    fim = inic + 7
    for objeto in lst_objetos:
        sheet_rotulos.write(inic,2,'Rótulo da região',style_ice) #escreve o texto= Rótulo da região
        sheet_rotulos.write(inic+1,2,objeto) #escreve o objeto encontrado 
        inic= fim
        fim = inic + 7
 
    #--------Informações WUP Entidades Fisicas-------------
    sheet_rotulos.col(3).width= 6800 #regula o tamanho da coluna em parenteses
    inic= 4
    fim = inic + 7
    for objeto in lst_objetos:
        dic_wup_fisicas= dicionario_wup_fisicas[objeto]   
        sheet_rotulos.write(inic,3,'TOP-5 WUP(Entidades Fisicas)',style_yellow) #escreve o texto= TOP-5 WUP(Entidades Fisicas)
        if dic_wup_fisicas[0].anotada is True: # Se a palavra estiver anotada
            sheet_rotulos.write(inic+1,3,dic_wup_fisicas[0].palavra,style_ocean_blue) # entidade 1
        else:
            sheet_rotulos.write(inic+1,3,dic_wup_fisicas[0].palavra) # entidade 1
        if dic_wup_fisicas[1].anotada is True: # Se a palavra estiver anotada    
            sheet_rotulos.write(inic+2,3,dic_wup_fisicas[1].palavra,style_ocean_blue) # entidade 2
        else:
            sheet_rotulos.write(inic+2,3,dic_wup_fisicas[1].palavra) # entidade 2
        if dic_wup_fisicas[2].anotada is True: # Se a palavra estiver anotada     
            sheet_rotulos.write(inic+3,3,dic_wup_fisicas[2].palavra,style_ocean_blue) # entidade 3
        else:
            sheet_rotulos.write(inic+3,3,dic_wup_fisicas[2].palavra) # entidade 3
        if dic_wup_fisicas[3].anotada is True: # Se a palavra estiver anotada    
            sheet_rotulos.write(inic+4,3,dic_wup_fisicas[3].palavra,style_ocean_blue) # entidade 4
        else:
            sheet_rotulos.write(inic+4,3,dic_wup_fisicas[3].palavra) # entidade 4
        if dic_wup_fisicas[4].anotada is True: # Se a palavra estiver anotada       
            sheet_rotulos.write(inic+5,3,dic_wup_fisicas[4].palavra,style_ocean_blue) # entidade 5
        else:
            sheet_rotulos.write(inic+5,3,dic_wup_fisicas[4].palavra) # entidade 5
        #valor WUP
        sheet_rotulos.write(inic,4,'VALOR WUP',style_green) #escreve o texto= VALOR WUP
        sheet_rotulos.write(inic+1,4,dic_wup_fisicas[0].valor) # valor 1
        sheet_rotulos.write(inic+2,4,dic_wup_fisicas[1].valor) # valor 2
        sheet_rotulos.write(inic+3,4,dic_wup_fisicas[2].valor) # valor 3
        sheet_rotulos.write(inic+4,4,dic_wup_fisicas[3].valor) # valor 4
        sheet_rotulos.write(inic+5,4,dic_wup_fisicas[4].valor) # valor 5
        inic= fim
        fim = inic + 7
    #--------Informações WUP Objetos-------------
    sheet_rotulos.col(5).width= 4900 #regula o tamanho da coluna em parenteses
    inic= 4
    fim = inic + 7
    for objeto in lst_objetos:
        dic_wup_objetos= dicionario_wup_objetos[objeto]  
        sheet_rotulos.write(inic,5,'TOP-5 WUP(Objetos)',style_pink) #escreve o texto= TOP-5 WUP(Objetos)
        if dic_wup_objetos[0].palavra in dicionario_dif_entidades_wup[objeto]:
            sheet_rotulos.write(inic+1,5,dic_wup_objetos[0].palavra,style_yellow) # entidade 1
            change_color_dif = True
        else:
            sheet_rotulos.write(inic+1,5,dic_wup_objetos[0].palavra) # entidade 1
        if dic_wup_objetos[1].palavra in dicionario_dif_entidades_wup[objeto]:
            sheet_rotulos.write(inic+2,5,dic_wup_objetos[1].palavra,style_yellow) # entidade 2
            change_color_dif = True
        else:
            sheet_rotulos.write(inic+2,5,dic_wup_objetos[1].palavra) # entidade 2
        if dic_wup_objetos[2].palavra in dicionario_dif_entidades_wup[objeto]:    
            sheet_rotulos.write(inic+3,5,dic_wup_objetos[2].palavra,style_yellow) # entidade 3
            change_color_dif = True
        else:
            sheet_rotulos.write(inic+3,5,dic_wup_objetos[2].palavra) # entidade 3
        if dic_wup_objetos[3].palavra in dicionario_dif_entidades_wup[objeto]:    
            sheet_rotulos.write(inic+4,5,dic_wup_objetos[3].palavra,style_yellow) # entidade 4
            change_color_dif = True
        else:
            sheet_rotulos.write(inic+4,5,dic_wup_objetos[3].palavra) # entidade 4
        if dic_wup_objetos[4].palavra in dicionario_dif_entidades_wup[objeto]: 
            sheet_rotulos.write(inic+5,5,dic_wup_objetos[4].palavra,style_yellow) # entidade 5
            change_color_dif = True
        else:
            sheet_rotulos.write(inic+5,5,dic_wup_objetos[4].palavra) # entidade 5
        #valor WUP
        sheet_rotulos.write(inic,6,'VALOR WUP',style_green) #escreve o texto= VALOR WUP
        sheet_rotulos.write(inic+1,6,dic_wup_objetos[0].valor) # valor 1
        sheet_rotulos.write(inic+2,6,dic_wup_objetos[1].valor) # valor 2
        sheet_rotulos.write(inic+3,6,dic_wup_objetos[2].valor) # valor 3
        sheet_rotulos.write(inic+4,6,dic_wup_objetos[3].valor) # valor 4
        sheet_rotulos.write(inic+5,6,dic_wup_objetos[4].valor) # valor 5
        inic= fim
        fim = inic + 7
    #--------Informações WE Entidades Fisicas-------------
    sheet_rotulos.col(7).width= 6800 #regula o tamanho da coluna em parenteses
    inic= 4
    fim = inic + 7
    for objeto in lst_objetos:
        dic_we_fisicas= dicionario_embeddings_fisicas[objeto]  
        sheet_rotulos.write(inic,7,'TOP-5 WE(Entidades Fisicas)',style_orange) #escreve o texto= TOP-5 WUP(Entidades Fisicas)
        if dic_we_fisicas[0].anotada is True: # Se a palavra estiver anotada
           sheet_rotulos.write(inic+1,7,dic_we_fisicas[0].palavra,style_ocean_blue) # entidade 1
        else:
           sheet_rotulos.write(inic+1,7,dic_we_fisicas[0].palavra) # entidade 1
        if dic_we_fisicas[1].anotada is True: # Se a palavra estiver anotada   
           sheet_rotulos.write(inic+2,7,dic_we_fisicas[1].palavra,style_ocean_blue) # entidade 2
        else:
           sheet_rotulos.write(inic+2,7,dic_we_fisicas[1].palavra) # entidade 2 
        if dic_we_fisicas[2].anotada is True: # Se a palavra estiver anotada      
           sheet_rotulos.write(inic+3,7,dic_we_fisicas[2].palavra,style_ocean_blue) # entidade 3
        else:
           sheet_rotulos.write(inic+3,7,dic_we_fisicas[2].palavra) # entidade 3
        if dic_we_fisicas[3].anotada is True: # Se a palavra estiver anotada    
           sheet_rotulos.write(inic+4,7,dic_we_fisicas[3].palavra,style_ocean_blue) # entidade 4
        else:
           sheet_rotulos.write(inic+4,7,dic_we_fisicas[3].palavra) # entidade 4 
        if dic_we_fisicas[4].anotada is True: # Se a palavra estiver anotada       
           sheet_rotulos.write(inic+5,7,dic_we_fisicas[4].palavra,style_ocean_blue) # entidade 5
        else:
           sheet_rotulos.write(inic+5,7,dic_we_fisicas[4].palavra) # entidade 5
        #valor WE
        sheet_rotulos.write(inic,8,'VALOR WE',style_green) #escreve o texto= VALOR WUP
        sheet_rotulos.write(inic+1,8,dic_we_fisicas[0].valor) # valor 1
        sheet_rotulos.write(inic+2,8,dic_we_fisicas[1].valor) # valor 2
        sheet_rotulos.write(inic+3,8,dic_we_fisicas[2].valor) # valor 3
        sheet_rotulos.write(inic+4,8,dic_we_fisicas[3].valor) # valor 4
        sheet_rotulos.write(inic+5,8,dic_we_fisicas[4].valor) # valor 5
        inic= fim
        fim = inic + 7
    #--------Informações WE Objetos-------------
    sheet_rotulos.col(9).width= 4900 #regula o tamanho da coluna em parenteses
    inic= 4
    fim = inic + 7
    for objeto in lst_objetos:
        dic_we_objetos= dicionario_embeddings_objetos[objeto]
        sheet_rotulos.write(inic,9,'TOP-5 WE(Objetos)',style_silver) #escreve o texto= TOP-5 WUP(Objetos)
        if dic_we_objetos[0].palavra in dicionario_dif_entidades_embeddings[objeto]:
            sheet_rotulos.write(inic+1,9,dic_we_objetos[0].palavra,style_yellow) # entidade 1
            change_color_dif = True
        else:
            sheet_rotulos.write(inic+1,9,dic_we_objetos[0].palavra) # entidade 1
        if dic_we_objetos[1].palavra in dicionario_dif_entidades_embeddings[objeto]:    
            sheet_rotulos.write(inic+2,9,dic_we_objetos[1].palavra,style_yellow) # entidade 2
            change_color_dif = True
        else:
            sheet_rotulos.write(inic+2,9,dic_we_objetos[1].palavra) # entidade 2
        if dic_we_objetos[2].palavra in dicionario_dif_entidades_embeddings[objeto]:     
            sheet_rotulos.write(inic+3,9,dic_we_objetos[2].palavra) # entidade 3
            change_color_dif = True
        else:
            sheet_rotulos.write(inic+3,9,dic_we_objetos[2].palavra) # entidade 3
        if dic_we_objetos[3].palavra in dicionario_dif_entidades_embeddings[objeto]:     
            sheet_rotulos.write(inic+4,9,dic_we_objetos[3].palavra,style_yellow) # entidade 4
            change_color_dif = True
        else:
           sheet_rotulos.write(inic+4,9,dic_we_objetos[3].palavra) # entidade 4 
        if dic_we_objetos[4].palavra in dicionario_dif_entidades_embeddings[objeto]:       
            sheet_rotulos.write(inic+5,9,dic_we_objetos[4].palavra,style_yellow) # entidade 5
            change_color_dif = True
        else:
            sheet_rotulos.write(inic+5,9,dic_we_objetos[4].palavra) # entidade 5
        #valor WE
        sheet_rotulos.write(inic,10,'VALOR WE',style_green) #escreve o texto= VALOR WUP
        sheet_rotulos.write(inic+1,10,dic_we_objetos[0].valor) # valor 1
        sheet_rotulos.write(inic+2,10,dic_we_objetos[1].valor) # valor 2
        sheet_rotulos.write(inic+3,10,dic_we_objetos[2].valor) # valor 3
        sheet_rotulos.write(inic+4,10,dic_we_objetos[3].valor) # valor 4
        sheet_rotulos.write(inic+5,10,dic_we_objetos[4].valor) # valor 5
        inic= fim
        fim = inic + 7
    #Escrevendo no sheet 'todas Entidades'
    sheet_todas_entidades = wb.add_sheet('Todas Entidades')

    #Informações do Rótulo
    sheet_todas_entidades.col(2).width= 7000
    sheet_todas_entidades.col(3).width= 7000
    sheet_todas_entidades.col(4).width= 4900
    sheet_todas_entidades.col(5).width= 4900

   
    sheet_todas_entidades.write(2,2,'Entidades Físicas',style_ice) #escreve o texto= Rótulo da região
    ini=3
    for entidades_fisicas in lst_entidades_fisicas:
        sheet_todas_entidades.write(ini,2,entidades_fisicas)
        ini += 1      
    sheet_todas_entidades.write(2,3,'Filtrada por OBJETOS',style_green) #escreve o objeto encontrado 
    ini=3
    for entidades_objetos in lst_entidades_objetos:
         sheet_todas_entidades.write(ini,3,entidades_objetos) #escreve o objeto encontrado 
         ini += 1
    sheet_todas_entidades.write(2,4,'Intersecção',style_lightOrange) #interseccao
    ini=3
    for entidades_interseccao in lst_entidades_interseccao:
       sheet_todas_entidades.write(ini,4,entidades_interseccao) 
       ini += 1
    sheet_todas_entidades.write(2,5,'Diferença',style_yellow) #escreve se a região foi correta ou incorreta
    ini=3
    for entidades_diferenca in lst_entidades_diferenca:
        sheet_todas_entidades.write(ini,5,entidades_diferenca) #escreve se a região foi correta ou incorreta
        ini += 1
    
    
    
        if noticia_anotada is False: # se não houve anotação, salva na pasta not_anotadas
               wb.save('info_news/not_anotadas/'+titulo_noticia+'.xls')
        else:
            if  change_color_dif is True:
                wb.save('info_news/objetos_diff/'+titulo_noticia+'.xls')
            else:
                wb.save('info_news/anotadas/'+titulo_noticia+'.xls')
