function output = createBoundary(datasetFile, states)
    tic
    dataset= importdata(datasetFile);
    
    % extracting features
    str = char(dataset(1));
    columns = strsplit(str, ',')
    number_of_features = length(columns) - 1

    d = dir('Clusters');
    dfolders = d([d(:).isdir]==1);
    dfolders = dfolders(~ismember({dfolders(:).name},{'.','..'}))

    states = {}
    for state = 1:length(dfolders)
        states = [ states dfolders(state).name ]
    end

    % creating directory for storing boundary points
    mkdir("Boundaries")
    for state = 1:length(states)
        for i = 0: number_of_features-2
            for j = i+1: number_of_features-1
                directories=dir("Clusters/"+states(state)+"/"+i+"_"+j);
                prefix="Clusters/"+states(state)+"/"+i+"_"+j;
                postfix="Boundaries/"+states(state)+"/"+i+"_"+j;

                files={}

                for f= 1 : length(directories)
                    if contains(directories(f).("name"),".txt")
                        files=[files directories(f).("name")]

                    end
                end
                mkdir(postfix)
                display(postfix)
                for f = 1: length(files)
                        data=load(prefix+"/"+files(f))
                        x= data(:,1);
                        y= data(:,2);

                        plot(x,y,'r.')
                        
                        % concave hull generation
                        k = boundary(x,y);
                        hold on;
                        plot(x(k),y(k));

                        hold on;
                        file=fopen(postfix+'/'+files(f),'w');
                        for l=1:length(k)
                            fprintf(file, '%f %f \n',[x(k(l)) y(k(l))]);
                        end
                        fclose(file)
                end            
            end
        end
    end
    timeElapsed = toc;
    display(timeElapsed)