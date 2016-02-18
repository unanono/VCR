# -*- coding: utf-8 *-*

from PythonMagick import Image
from pyPdf import PdfFileReader
#import PythonMagick

DBHost = 'localhost'
DBPort = 27017
DBAdminUser = None
DBAdminPassword = None

#TemplatesFolder = os.path.join(here, 'templates/')
TemplatesFolder = 'templates/'
UploadsFolder = 'uploads/'
#Nombre de la cookie de sesion
cookieSessionName = 'session'
defaultImageExtension = '.png'


def slideImage(user, name, number):
    sn = name + str(number) + defaultImageExtension
    return uploadDirectory(user + '/' + sn)


def uploadDirectory(FileName):
    return ''.join([UploadsFolder, FileName])


def templateName(TemplateFile):
    ''' Devuelve el archivo del template con el path correcto '''
    return ''.join([TemplatesFolder, TemplateFile])


def getPdfNumPages(name):
    with open(name) as f:
        pdfFile = PdfFileReader(f)
        return pdfFile.getNumPages()


def pdf2images(name):
    np = getPdfNumPages(name)
    for p in range(np):
        i = Image()
        i.density('200')
        i.quality(100)
        i.depth(24)
        #i.backgroundColor(
        #i.channel(
        i.read(name + '[' + str(p) + ']')
        i.write(name + str(p) + defaultImageExtension)


if __name__ == '__main__':
    pdf2images('pp.pdf')
