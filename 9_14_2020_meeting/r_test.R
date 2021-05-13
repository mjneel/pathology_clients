library("readxl")
library("ggbiplot")
library('devtools')
setwd("D:/MonukiLab/9.14.2020 meeting data")

# reading data and formatting it accordingly
data = read_excel("PCA.xlsx", col_types ="numeric")
data = t(data)
colnames(data) = c("Drops", "Spears", "Green Spears", "Rods", "Green Rods", "Crescents", "Rings", "Saturns", "Oreos", "Kettlebells", "Multi Speck", "Multi Spear", "GR", "MP", "MAF")
data = data[-1,]
data

data.pca = prcomp(data[,c(1:15)], center = TRUE, scale. = TRUE)

data.pca = (data.pca[1])
summary(data.pca)

ggbiplot(data.pca, labels = rownames(data), alpha = 0, x = "PC5")

ggscreeplot(data.pca)

library("FactoMineR")
library("factoextra")

fviz_pca_var(data.pca, repel = TRUE, axes = c(2,3))

fviz_pca_biplot(data.pca, repel = TRUE, col.var = "#2E9FDF", col.ind = "#696969", axes = c(2,3))

fviz_pca_ind(data.pca, repel = TRUE, axes = c(2,3))
